import json
import logging

from sqlalchemy.inspection import inspect
from sqlalchemy.schema import Column
from unrest.coercers import Serialize

log = logging.getLogger('unrest')


class RestError(Exception):
    def __init__(self, message, status):
        self.message = message
        self.status = status


class Rest(object):
    """Model path on /root_path/schema/model if schema is not public"""
    def __init__(self, unrest, Model,
                 methods=['GET'], name=None, only=None, exclude=None):
        self.unrest = unrest
        self.Model = Model
        self.name = name or self.table.name
        self.methods = methods
        self.only = only
        self.exclude = exclude

        for method in methods:
            self.register_method(method)

    def get(self, payload, **kwargs):
        if kwargs:
            pks = self.kwargs_to_pks(kwargs)
            model = self.Model.query.get(pks)
            if model is None:
                raise RestError(
                    '%s(%s) not found' % (self.name, pks), 404)

            return self.serialize(model)

        models = self.Model.query
        return self.serialize_all(models)

    def post(self, payload, **kwargs):
        pks = self.kwargs_to_pks(kwargs)
        return 'POST %s %s' % ('.'.join(self.name_parts), pks)

    def put(self, payload, **kwargs):
        pks = self.kwargs_to_pks(kwargs)
        return 'PUT %s %s' % ('.'.join(self.name_parts), pks)

    def delete(self, payload, **kwargs):
        pks = self.kwargs_to_pks(kwargs)
        return 'DELETE %s %s' % ('.'.join(self.name_parts), pks)

    def kwargs_to_pks(self, kwargs):
        return tuple(kwargs.get(pk.name) for pk in self.primary_keys)

    def serialize(self, model):
        return Serialize(model, self.columns).dict()

    def serialize_all(self, query):
        return {
            'occurences': query.count(),
            'objects': [
                self.serialize(model) for model in query  # Pagination ?
            ]
        }

    def wrap_native(self, method):
        def wrapped(**kwargs):
            json = self.unrest.framework.request_json()
            payload = self.unjson(json)
            try:
                data = method(payload, **kwargs)
            except RestError as e:
                json = {'message': e.message}
                return self.unrest.framework.send_error({'message': e.message}, e.stat)
            json = self.json(data)
            return self.unrest.framework.send_json(json)
        return wrapped

    def register_method(self, method, method_fun=None):
            method_fun = method_fun or getattr(self, method.lower())
            method_fun = self.wrap_native(method_fun)
            method_fun.__name__ = '_'.join(
                (method_fun.__name__,) + self.name_parts)
            self.unrest.framework.register_route(
                self.path, method, self.primary_keys,
                method_fun)

    def json(self, data):
        return json.dumps(data)

    def unjson(self, data):
        if data:
            return json.loads(data)

    @property
    def name_parts(self):
        if self.table.schema:
            return (self.table.schema, self.table.name)
        return (self.table.name,)

    @property
    def path(self):
        return '%s%s' % (
            self.unrest.root_path,
            '/'.join(self.name_parts))

    @property
    def table(self):
        return self.Model.__table__

    @property
    def primary_keys(self):
        return inspect(self.Model).primary_key

    @property
    def model_columns(self):
        for column in inspect(self.Model).columns:
            if isinstance(column, Column):
                yield column

    @property
    def columns(self):
        for column in self.model_columns:
            if column.name not in [pk.name for pk in self.primary_keys]:
                if self.only and column.name not in self.only:
                    continue
                if self.exclude and column.name in self.exclude:
                    continue
            yield column


class UnRest(object):
    """Root path on /path/version/ if version else /path/ """
    def __init__(self, app=None, path='/api', version='', framework=None):
        self.app = app
        self.path = path
        self.version = version
        if framework:
            self.framework = framework(app)
        else:
            try:
                from flask import Flask
            except ImportError:
                pass
            else:
                if isinstance(app, Flask):
                    from .flask import FlaskUnRest
                    self.framework = FlaskUnRest(app)
        if not self.framework:
            raise NotImplemented(
                'Your framework %s is not recognized. '
                'Please provide a framework argument to UnRest' % type(app))

    def init_app(self, app):
        self.app = app

    @property
    def root_path(self):
        return '/'.join((self.path, self.version))

    def __call__(self, *args, **kwargs):
        rest = Rest(self, *args, **kwargs)
        return rest
