c2c.sqlalchemy.rest
===================

Use it
------

Example::

    class Object(Base)
        __tablename__ = 'object'
        __table_args__ = {'autoload':True}
        __acl__ = [
            (Allow, 'admin', ALL_PERMISSIONS),
            (Allow, 'editor', ('view', 'edit', 'new', 'delete')),
            (Allow, Authenticated, ('view')),
        ]

    from pyramid.renderers import JSONP
    config.add_renderer('jsonp', JSONP(param_name='callback'))

    from c2c.sqlalchemy.rest import REST, add_rest_routes
    obj = REST(DBSession, Object)

    @view_config(route_name='obj_read_many', renderer='jsonp')
    def obj_read_many(request):
        return obj.read_many(request)

    @view_config(route_name='obj_read_one', renderer='jsonp')
    def obj_read_one(request):
        return obj.read_one(request)

    @view_config(route_name='obj_count', renderer='jsonp')
    def obj_count(request):
        return obj.count(request)

    @view_config(route_name='obj_create', renderer='jsonp')
    def obj_create(request):
        return obj.create(request)

    add_rest_routes(config, 'obj', '/object')

From source
-----------

Build::

    python bootstrap.py --distribute -v 1.7.1
    ./buildout/bin/buildout
