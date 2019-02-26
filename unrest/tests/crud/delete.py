from .. import idsorted
from ...unrest import UnRest
from ..model import Fruit, Tree


class DeleteTestCollection(object):
    def test_delete_tree_implicitly_unallowed(self):
        rest = UnRest(self.app, self.session, framework=self.__framework__)
        rest(Tree, methods=['GET', 'DELETE'])
        code, json = self.fetch('/api/tree', method="DELETE")
        assert code == 406

    def test_delete_tree(self):
        rest = UnRest(self.app, self.session, framework=self.__framework__)
        rest(Tree, methods=['GET', 'DELETE'], allow_batch=True)
        code, json = self.fetch('/api/tree', method="DELETE")
        assert code == 200
        assert json['occurences'] == 3
        assert idsorted(json['objects']) == [
            {'id': 1, 'name': 'pine'},
            {'id': 2, 'name': 'maple'},
            {'id': 3, 'name': 'oak'},
        ]

        code, json = self.fetch('/api/tree')
        assert code == 200
        assert json['occurences'] == 0
        assert idsorted(json['objects']) == []

    def test_delete_fruits(self):
        rest = UnRest(self.app, self.session, framework=self.__framework__)
        rest(Fruit, methods=['GET', 'DELETE'], allow_batch=True)
        code, json = self.fetch('/api/fruit', method="DELETE")
        assert code == 200
        assert json['occurences'] == 5
        assert idsorted(json['objects'], 'fruit_id') == [
            {
                'fruit_id': 1,
                'color': 'grey',
                'size': 12.0,
                'double_size': 24.0,
                'age': 1_041_300.0,
                'tree_id': 1,
            },
            {
                'fruit_id': 2,
                'color': 'darkgrey',
                'size': 23.0,
                'double_size': 46.0,
                'age': 4_233_830.213,
                'tree_id': 1,
            },
            {
                'fruit_id': 3,
                'color': 'brown',
                'size': 2.12,
                'double_size': 4.24,
                'age': 0.0,
                'tree_id': 1,
            },
            {
                'fruit_id': 4,
                'color': 'red',
                'size': 0.5,
                'double_size': 1.0,
                'age': 2400.0,
                'tree_id': 2,
            },
            {
                'fruit_id': 5,
                'color': 'orangered',
                'size': 100.0,
                'double_size': 200.0,
                'age': 7200.000_012,
                'tree_id': 2,
            },
        ]

        code, json = self.fetch('/api/fruit')
        assert code == 200
        assert json['occurences'] == 0
        assert idsorted(json['objects']) == []