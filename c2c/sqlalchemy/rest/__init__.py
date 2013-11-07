# -*- coding: utf-8 -*-

import datetime
from json import loads
from sqlalchemy import or_
from sqlalchemy.orm.util import class_mapper
from sqlalchemy.ext.associationproxy import _AssociationList
from sqlalchemy.orm.properties import ColumnProperty, RelationshipProperty
from sqlalchemy.orm.exc import NoResultFound
from pyramid.response import Response
from pyramid.security import has_permission
from pyramid.httpexceptions import HTTPNotFound, HTTPForbidden, HTTPBadRequest
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
        route_name = route_name_prefix + '_auto'
        config.add_route(route_name, base_url + '/auto', request_method='POST')
    route_name = route_name_prefix + '_update'
    config.add_route(route_name, base_url + '/{id:\\d+}', request_method='PUT')
    route_name = route_name_prefix + '_delete'
    config.add_route(route_name, base_url + '/{id:\\d+}', request_method='DELETE')


class REST(object):
    def __init__(self, session, mapped_class, children=None):
        self.session = session
        self.mapped_class = mapped_class

        self.columns = []
        self.relationships = {}
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
            elif children is not None and \
                    isinstance(p, RelationshipProperty) and \
                    p.key in children.keys():
                rel = children[p.key]
                if 'rest' not in rel or not isinstance(rel['rest'], REST):
                    raise HTTPBadRequest("Missing REST object for relationship %s"
                        % p.key)
                self.relationships[p.key] = rel

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
        for key in self.relationships:
            rel = self.relationships[key]
            attr = getattr(obj, key)
            if hasattr(attr, '__iter__'):
                data = [rel['rest']._properties(o) for o in attr]
            else:
                data = rel['rest']._properties(attr)
            propname = rel['propname'] if 'propname' in rel else key
            properties[propname] = data
        if hasattr(obj, '__additional_properties__'):
            properties.update(obj.__additional_properties__)
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

    def _fill_properties(self, request, session, obj, set_id=False):
        body = loads(request.body)
        if set_id and self.id in body:
            setattr(obj, self.id, body[self.id])
        for col in self.columns:
            if col in body:
                setattr(obj, col, body[col])
        for key in self.relationships:
            rel = self.relationships[key]
            propname = rel['propname'] if 'propname' in rel else key
            if propname in body:
                ids = body[propname]
                if not isinstance(ids, list):
                    ids = [ids]
                if len(ids) > 0:
                    rest = rel['rest']
                    clause = or_(*[getattr(rest.mapped_class, rest.id)==int(id) for id in ids])
                    children = session.query(rest.mapped_class).filter(clause).all()
                else:
                    children = []
                setattr(obj, key, children)

    def create(self, request):
        if has_permission('new', self.mapped_class, request) \
                or not hasattr(self.mapped_class, '__acl__'):
            session = self.session()
            obj = self.mapped_class()
            self._fill_properties(request, session, obj)
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
            self._fill_properties(request, session, obj)
            session.flush()
            return Response(status_int=202)
        raise HTTPForbidden()

    def auto(self, request):
        if has_permission('edit', self.mapped_class, request) \
                or not hasattr(self.mapped_class, '__acl__'):
            session = self.session()
            obj = None
            body = loads(request.body)
            
            if self.id not in body:
                raise HTTPBadRequest('Mandatory attribute %s is missing'
                    % self.id)
            
            try:
                id = int(body[self.id])
            except:
                raise HTTPBadRequest('Attribute %s must be an integer'
                    % self.id)
            query = session.query(self.mapped_class)
            query = query.filter(getattr(self.mapped_class, self.id) == id)
            try:
                obj = query.one()
            except NoResultFound:
                pass

            if obj is None:
                obj = self.mapped_class()
                self._fill_properties(request, session, obj, True)
                session.add(obj)
                status_int=201
            else:
                self._fill_properties(request, session, obj)
                status_int=202
            
            session.flush()
            return Response(status_int=status_int)
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
