import sys

from sqlalchemy.types import Float, String

from unrest import UnRest, __about__
from unrest.coercers import Deserialize, Serialize
from unrest.framework.flask import FlaskFramework
from unrest.rest import Rest

from . import idsorted
from ...framework import Framework
from ...idiom import Idiom
from ...util import Response
from ..model import Fruit, Tree
from .openapi_result import openapi


def test_index(app, db, http):
    rest = UnRest(app, db.session)
    rest(Tree)
    code, json = http.get('/api/')
    assert code == 200
    assert (
        json['html']
        == (
            '<h1>unrest <small>api server</small></h1> version %s '
            '<a href="https://github.com/Kozea/unrest">unrest</a> '
            '<a href="/api/openapi.json">openapi.json</a>'
        )
        % __about__.__version__
    )


def test_normal(app, db, http):
    rest = UnRest(app, db.session)
    rest(Tree)
    code, json = http.get('/api/tree')
    assert code == 200
    assert json['occurences'] == 3


def test_path(app, db, http):
    rest = UnRest(app, db.session, '/forest')
    rest(Tree)
    code, json = http.get('/forest/tree')
    assert code == 200
    assert json['occurences'] == 3


def test_version(app, db, http):
    rest = UnRest(app, db.session, version='v3.14')
    rest(Tree)
    code, json = http.get('/api/v3.14/tree')
    assert code == 200
    assert json['occurences'] == 3


def test_path_and_version(app, db, http):
    rest = UnRest(app, db.session, '/forest', 'v3.14')
    rest(Tree)
    code, json = http.get('/forest/v3.14/tree')
    assert code == 200
    assert json['occurences'] == 3


def test_explicit_framework(app, db, http):
    rest = UnRest(app, db.session, framework=FlaskFramework)
    rest(Tree)
    code, json = http.get('/api/tree')
    assert code == 200
    assert json['occurences'] == 3


def test_normal_rest_class(app, db, http):
    rest = UnRest(app, db.session, framework=FlaskFramework)
    tree = rest(Tree, name='tree')
    assert isinstance(tree, Rest)


def test_alternative_rest_class(app, db, http):
    class NewRest(Rest):
        def __init__(self, *args, **kwargs):
            kwargs['name'] = 'new_' + kwargs['name']
            super().__init__(*args, **kwargs)

    new_rest = UnRest(
        app, db.session, framework=FlaskFramework, RestClass=NewRest
    )
    new_tree = new_rest(Tree, name='tree')
    assert isinstance(new_tree, NewRest)

    code, json = http.get('/api/tree')
    assert code == 404
    code, json = http.get('/api/new_tree')
    assert code == 200
    assert json['occurences'] == 3


def test_empty_get_pk_as_404(app, db, http):
    rest = UnRest(
        app, db.session, framework=FlaskFramework, empty_get_as_404=True
    )
    rest(Tree)
    code, json = http.get('/api/tree/6')
    assert code == 404
    assert json['occurences'] == 0
    assert json['objects'] == []


def test_empty_explicit_framework(app, db, http):
    class FakeUnRest(object):
        def __init__(self, app, prefix):
            pass

        def register_route(self, *args, **kwargs):
            pass

    rest = UnRest(app, db.session, framework=FakeUnRest)
    rest(Tree)
    code, _ = http.get('/api/tree')
    assert code == 404


def test_api_options(app, db, http):
    rest = UnRest(app, db.session)
    fruit = rest(Fruit)
    rest(
        Tree,
        methods=rest.all,
        relationships={'fruits': fruit},
        properties=['fruit_colors'],
        allow_batch=True,
    )
    code, json = http.options('/api')
    assert code == 200
    assert json == {
        '/api/fruit': {
            'model': 'Fruit',
            'description': 'A bag of fruit',
            'parameters': ['fruit_id'],
            'columns': {
                'age': 'timedelta',
                'color': 'str',
                'fruit_id': 'int',
                'size': 'Decimal',
                'tree_id': 'int',
                'double_size': 'Decimal',
            },
            'properties': {},
            'relationships': {},
            'methods': ['GET', 'OPTIONS'],
            'batch': False,
        },
        '/api/tree': {
            'model': 'Tree',
            'description': "Where money doesn't grow",
            'parameters': ['id'],
            'columns': {'id': 'int', 'name': 'str'},
            'properties': {'fruit_colors': 'str'},
            'relationships': {
                'fruits': {
                    'model': 'Fruit',
                    'description': 'A bag of fruit',
                    'parameters': ['fruit_id'],
                    'columns': {
                        'age': 'timedelta',
                        'color': 'str',
                        'fruit_id': 'int',
                        'size': 'Decimal',
                        'tree_id': 'int',
                        'double_size': 'Decimal',
                    },
                    'properties': {},
                    'relationships': {},
                    'batch': False,
                }
            },
            'methods': ['GET', 'PUT', 'POST', 'DELETE', 'PATCH', 'OPTIONS'],
            'batch': True,
        },
    }


def test_endpoint_options(app, db, http):
    rest = UnRest(app, db.session, framework=FlaskFramework)
    fruit = rest(Fruit)
    rest(
        Tree,
        methods=rest.all,
        relationships={'fruits': fruit},
        properties=['fruit_colors'],
        allow_batch=True,
    )
    code, json = http.options('/api/fruit')
    assert code == 200
    assert json == {
        'model': 'Fruit',
        'description': 'A bag of fruit',
        'batch': False,
        'parameters': ['fruit_id'],
        'columns': {
            'age': 'timedelta',
            'color': 'str',
            'fruit_id': 'int',
            'size': 'Decimal',
            'tree_id': 'int',
            'double_size': 'Decimal',
        },
        'properties': {},
        'relationships': {},
        'methods': ['GET', 'OPTIONS'],
    }


def test_openapi(app, db, http):
    rest = UnRest(
        app,
        db.session,
        info={
            'description': '''# Unrest demo
This is the demo of unrest api.
This api expose the `Tree` and `Fruit` entity Rest methods.
''',
            'contact': {
                'name': __about__.__author__,
                'url': __about__.__uri__,
                'email': __about__.__email__,
            },
            'license': {'name': __about__.__license__},
        },
    )
    fruit = rest(
        Fruit,
        methods=rest.all,
        properties=[rest.Property('square_size', Float())],
    )
    rest(
        Tree,
        methods=rest.all,
        relationships={'fruits': fruit},
        properties=['fruit_colors'],
        allow_batch=True,
    )

    code, json = http.get('/api/openapi.json')
    assert code == 200
    assert json == openapi


def test_sub(app, db, http):
    rest = UnRest(app, db.session)

    fruit = rest(
        Fruit,
        methods=rest.all,
        properties=[rest.Property('square_size', Float())],
    )
    tree = rest(
        Tree,
        methods=rest.all,
        relationships={'fruits': fruit},
        properties=['fruit_colors'],
        query=lambda q: q.filter(Tree.name != 'pine'),
        allow_batch=True,
    )
    subtree = tree.sub(lambda q: q.filter(Tree.name != 'oak'))
    for key in [
        'unrest',
        'Model',
        'methods',
        'only',
        'exclude',
        'properties',
        'relationships',
        'allow_batch',
        'auth',
        'read_auth',
        'write_auth',
        'validators',
        '_primary_keys',
        'SerializeClass',
        'DeserializeClass',
    ]:
        assert getattr(subtree, key) == getattr(tree, key)
    assert subtree.name == 'subtree'

    code, json = http.get('/api/tree')
    assert code == 200
    assert json['occurences'] == 2

    code, json = http.get('/api/subtree')
    assert code == 200
    assert json['occurences'] == 1

    subtree = tree.sub(
        lambda q: q.filter(Tree.name != 'maple'), name='nomaple'
    )
    code, json = http.get('/api/nomaple')
    assert code == 200
    assert json['occurences'] == 1


def test_sub_fixed(app, db, http):
    rest = UnRest(app, db.session)

    fruit = rest(
        Fruit,
        defaults={'size': 1.0},
        fixed={'color': 'blue'},
        methods=rest.all,
        properties=[rest.Property('square_size', Float())],
    )
    subfruit = fruit.sub(lambda q: q.filter(Fruit.age == 2.0))
    for key in ['defaults', 'fixed']:
        assert getattr(subfruit, key) == getattr(fruit, key)


def test_idiom(app, db, http):
    class FakeIdiom(Idiom):
        def request_to_payload(self, request):
            if request.method == 'PUT':
                return {'name': 'sth'}

        def data_to_response(self, data, method, status=200):
            payload = 'Hello %d' % data['occurences']
            headers = {'Content-Type': 'text/plain'}
            response = Response(payload, headers, status)
            return response

    rest = UnRest(app, db.session, idiom=FakeIdiom)
    rest(Tree, methods=['GET', 'PUT'])
    code, json = http.get('/api/tree')
    assert code == 200
    assert json['html'] == 'Hello 3'

    code, json = http.put('/api/tree/1')
    assert code == 200
    assert json['html'] == 'Hello 1'

    code, json = http.get('/api/tree')
    assert code == 200
    assert json['html'] == 'Hello 3'


def test_wrong_framework(app, db, http):
    try:
        UnRest(app, db.session, framework=Framework)
    except NotImplementedError:
        pass
    else:
        raise Exception('Should have raised')  # pragma: no cover


def test_no_framework(app, db, http):
    flask = sys.modules['flask']
    sys.modules['flask'] = None
    try:
        UnRest(app, db.session)
    except NotImplementedError:
        pass
    else:
        raise Exception('Should have raised')  # pragma: no cover
    sys.modules['flask'] = flask


def test_custom_serialization(app, db, http):
    class UpperCaseStringSerialize(Serialize):
        def serialize(self, name, column):
            rv = super().serialize(name, column)
            if isinstance(column.type, String):
                return rv.upper()
            return rv

    rest = UnRest(app, db.session, SerializeClass=UpperCaseStringSerialize)
    rest(Tree, methods=['GET', 'PUT'])

    code, json = http.get('/api/tree')
    assert code == 200
    assert json['occurences'] == 3
    assert idsorted(json['objects']) == [
        {'id': 1, 'name': 'PINE'},
        {'id': 2, 'name': 'MAPLE'},
        {'id': 3, 'name': 'OAK'},
    ]


def test_custom_deserialization(app, db, http):
    class UpperCaseStringDeserialize(Deserialize):
        def deserialize(self, name, column, payload=None):
            rv = super().deserialize(name, column, payload)
            if isinstance(column.type, String):
                return rv.upper()
            return rv

    rest = UnRest(app, db.session, DeserializeClass=UpperCaseStringDeserialize)
    rest(Tree, methods=['GET', 'PUT'])

    code, json = http.put('/api/tree/1', json={'id': 1, 'name': 'cedar'})
    assert code == 200
    assert json['occurences'] == 1
    assert idsorted(json['objects']) == [{'id': 1, 'name': 'CEDAR'}]

    code, json = http.get('/api/tree')
    assert code == 200
    assert json['occurences'] == 3
    assert idsorted(json['objects']) == [
        {'id': 1, 'name': 'CEDAR'},
        {'id': 2, 'name': 'maple'},
        {'id': 3, 'name': 'oak'},
    ]
