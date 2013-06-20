c2c.sqlalchemy.rest
===================

Use it
------

In ``<project>/model.py``:

.. code:: python

    from pyramid.security import Allow, Authenticated, ALL_PERMISSIONS
    class Object(Base):
        __tablename__ = 'object'
        __table_args__ = {'autoload':True}
        __acl__ = [
            (Allow, 'admin', ALL_PERMISSIONS),
            (Allow, 'editor', ('view', 'edit', 'new', 'delete')),
            (Allow, Authenticated, ('view')),
        ]

In ``<project>/views/rest.py``:

.. code:: python

    from pyramid.view import view_config
    from c2c.sqlalchemy.rest import REST
    from <project>.models import DBSession, Object
    obj = REST(DBSession, Object)

    @view_config(route_name='obj_read_many', renderer='jsonp')
    def obj_read_many(request):
        return obj.read_many(request)

    @view_config(route_name='obj_read_one', renderer='jsonp')
    def obj_read_one(request):
        return obj.read_one(request)

    @view_config(route_name='obj_count', renderer='string')
    def obj_count(request):
        return obj.count(request)

    @view_config(route_name='obj_create', renderer='jsonp')
    def obj_create(request):
        return obj.create(request)

    @view_config(route_name='obj_update')
    def obj_update(request):
        return obj.update(request)

    @view_config(route_name='obj_delete', renderer='jsonp')
    def obj_delete(request):
        return obj.delete(request)

In ``<project>/__init__.py``:

.. code:: python

    from pyramid.renderers import JSONP
    from c2c.sqlalchemy.rest import add_rest_routes
    config.add_renderer('jsonp', JSONP(param_name='callback'))
    add_rest_routes(config, 'obj', '/object')

From source
-----------

Build::

    python bootstrap.py --distribute -v 1.7.1
    ./buildout/bin/buildout

Protocol
--------

Read many, ``GET`` on ``.../obj``:

.. code:: javascript

    {
        "objects": [{
            "id": id,
            "property": "value",
            ...
        },
        ...
        ]
    }

Read one, ``GET`` on ``.../obj/{id}``:

.. code:: javascript

    {
        "id": id,
        "property": "value",
        ...
    }

Count, ``GET`` on ``.../obj/count``:

.. code:: javascript

    23

Create, ``POST`` on ``.../obj`` with data:

.. code:: javascript

    {
        "property": "value",
        ...
    }

and it will return the id.

Update, ``PUT`` on ``.../obj/{id}`` with data:

.. code:: javascript

    {
        "property": "value",
        ...
    }

Delete, ``DELETE`` on ``.../obj/{id}``.
