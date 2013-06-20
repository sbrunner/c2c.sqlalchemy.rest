# -*- coding: utf-8 -*-

import datetime
from json import loads
from sqlalchemy.orm.util import class_mapper
from sqlalchemy.ext.associationproxy import _AssociationList
from sqlalchemy.orm.properties import ColumnProperty
from sqlalchemy.orm.exc import NoResultFound
from pyramid.response import Response
from pyramid.security import has_permission
from pyramid.httpexceptions import HTTPNotFound, HTTPForbidden
from geoalchemy.postgis import PGPersistentSpatialElement
from shapely.wkb import loads as loadsWKB

def add_rest_routes(config, route_name_prefix, base_url, create=True):
    route_name = route_name_prefix + '_read_many'
    config.add_route(route_name, base_url, request_method='GET')
    route_name = route_name_prefix + '_count'
    config.add_route(route_name, base_url + '/count', request_method='GET')
    route_name = route_name_prefix + '_read_one'
    config.add_route(route_name, base_url + '/{id:\\d+}', request_method='GET')
    if create:
        route_name = route_name_prefix + '_create'
        config.add_route(route_name, base_url, request_method='POST')
    route_name = route_name_prefix + '_update'
    config.add_route(route_name, base_url + '/{id:\\d+}', request_method='PUT')
    route_name = route_name_prefix + '_delete'
    config.add_route(route_name, base_url + '/{id:\\d+}', request_method='DELETE')


class REST(object):
    def __init__(self, session, mapped_class):
        self.session = session
        self.mapped_class = mapped_class

        self.columns = []
        self.id = None

        for p in class_mapper(mapped_class).iterate_properties:
            if isinstance(p, ColumnProperty):
                if len(p.columns) != 1:
                    raise NotImplementedError
                col = p.columns[0]
                if col.primary_key:
                    self.id = p.key
                elif not col.foreign_keys:
                    self.columns.append(p.key)

    def _properties(self, obj):
        properties = {}
        for col in self.columns:
            attr = getattr(obj, col)
            if isinstance(attr, (datetime.date, datetime.datetime)):
                attr = attr.isoformat()
            elif isinstance(attr, _AssociationList):
                attr = list(attr)
            elif isinstance(attr, PGPersistentSpatialElement):
                attr = loadsWKB(str(attr.geom_wkb))
            properties[col] = attr
        properties[self.id] = getattr(obj, self.id)
        return properties

    def read_many(self, request):
        if has_permission('view', self.mapped_class, request) \
                or not hasattr(self.mapped_class, '__acl__'):
            query = self.session().query(self.mapped_class)
            return {
                "objects": [self._properties(o) for o in query.all()]
            }
        raise HTTPForbidden()

    def _read_one(self, request, session=None):
        if not session:
            session = self.session()
        id = request.matchdict.get('id', None)
        query = session.query(self.mapped_class)
        query = query.filter(getattr(self.mapped_class, self.id) == int(id))
        try:
            o = query.one()
            return o
        except NoResultFound:
            raise HTTPNotFound("No %s found with id: %s." % (
                self.mapped_class.__name__,
                id
            ))

    def read_one(self, request):
        if has_permission('view', self.mapped_class, request) \
                or not hasattr(self.mapped_class, '__acl__'):
            o = self._read_one(request)
            return self._properties(o)
        raise HTTPForbidden()

    def count(self, request):
        if has_permission('view', self.mapped_class, request) \
                or not hasattr(self.mapped_class, '__acl__'):
            return self.session().query(self.mapped_class).count()
        raise HTTPForbidden()

    def create(self, request):
        if has_permission('new', self.mapped_class, request) \
                or not hasattr(self.mapped_class, '__acl__'):
            body = loads(request.body)
            session = self.session()
            obj = self.mapped_class()
            for col in self.columns:
                if col in body:
                    setattr(obj, col, body[col])
            session.add(obj)
            session.flush()
            request.response.status_int = 201
            return getattr(obj, self.id)
        raise HTTPForbidden()

    def update(self, request):
        if has_permission('edit', self.mapped_class, request) \
                or not hasattr(self.mapped_class, '__acl__'):
            session = self.session()
            obj = self._read_one(request, session)
            body = loads(request.body)
            for col in self.columns:
                if col in body:
                    setattr(obj, col, body[col])
            session.flush()
            return Response(status_int=202)
        raise HTTPForbidden()

    def delete(self, request):
        if has_permission('delete', self.mapped_class, request) \
                or not hasattr(self.mapped_class, '__acl__'):
            session = self.session()
            obj = self._read_one(request, session)
            session.delete(obj)
            session.flush()
            return Response(status_int=204)
        raise HTTPForbidden()
