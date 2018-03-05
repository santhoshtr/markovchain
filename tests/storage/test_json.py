from io import StringIO
from collections import deque
import pytest

from markovchain import JsonStorage


def test_json_storage_empty():
    storage = JsonStorage()
    assert storage.nodes == {}
    assert storage.settings == {}

def test_json_storage_get_dataset():
    storage = JsonStorage()
    with pytest.raises(KeyError):
        storage.get_dataset('0')
    data = storage.get_dataset('0', True)
    assert data == {}
    assert storage.get_dataset('0', True) is data
    assert storage.get_dataset('1', True) is not data

def test_json_storage_add_links():
    storage = JsonStorage()
    storage.add_links([
        ('0', ('x',), 'y'),
        ('0', ('y',), 'z'),
        ('0', ('x',), 'y')
    ])
    assert storage.nodes == {
        '0': {
            'x': [2, 'y'],
            'y': [1, 'z']
        }
    }
    storage.add_links([
        ('0', ('z',), 'x'),
        ('0', ('x',), 'z'),
        ('0', ('x',), 'y')
    ])
    assert storage.nodes == {
        '0': {
            'x': [[3, 1], ['y', 'z']],
            'y': [1, 'z'],
            'z': [1, 'x']
        }
    }
    storage.add_links([
        ('1', ('x',), 'y')
    ])
    assert storage.nodes == {
        '0': {
            'x': [[3, 1], ['y', 'z']],
            'y': [1, 'z'],
            'z': [1, 'x']
        },
        '1': {
            'x': [1, 'y']
        }
    }

@pytest.mark.parametrize('state,size,res', [
    ([], 4, ['', '', '', '']),
    (['ab', 'cd'], 1, ['cd']),
    (['ab', 'cd'], 3, ['', 'ab', 'cd'])
])
def test_json_storage_get_state(state, size, res):
    storage = JsonStorage()
    assert storage.get_state(state, size) == deque(res, maxlen=size)

@pytest.mark.parametrize('args,res', [
    ((['x'],), [(1, 'y')]),
    ((['x', 'y'],), [(1, 'z')]),
    ((['y'],), [(1, 'x'), (2, 'y'), (3, 'z')]),
    ((['z'],), [])
])
def test_json_storage_get_links(args, res):
    nodes = {
        'x': [1, 'y'],
        'y': [[1, 2, 3], ['x', 'y', 'z']],
        'x y': [1, 'z'],
    }
    storage = JsonStorage()
    assert storage.get_links(nodes, *args) == res

@pytest.mark.parametrize('args,res', [
    (((0, 'y'), deque(['x'])), ['x', 'y']),
    (((0, 'y'), deque(['x']), True), ['y', 'x']),
])
def test_json_storage_follow_link(args, res):
    storage = JsonStorage()
    assert storage.follow_link(*args) == deque(res)

def test_json_storage_state_separator():
    storage = JsonStorage()
    storage.add_links([('0', ('x', 'y'), 'z'), ('1', ('y', 'z'), 'x')])
    assert storage.nodes == {
        '0': {
            'x y': [1, 'z']
        },
        '1': {
            'y z': [1, 'x']
        }
    }
    storage.state_separator = ':'
    assert storage.nodes == {
        '0': {
            'x:y': [1, 'z'],
        },
        '1': {
            'y:z': [1, 'x']
        }
    }

@pytest.mark.parametrize('test,test2,res', [
    ((), (), True),
    ((), ({}), True),
    ((), ({'0': {'x':[1, 'y']}}), False),
    (({'0': {'x':[1, 'y']}}), ({'0': {'x':[1, 'y']}}), True),
    ((), ({}, {'state_separator': ':'}), False)
])
def test_json_storage_eq(test, test2, res):
    assert (JsonStorage(*test) == JsonStorage(*test2)) == res

def test_json_storage_save_load():
    storage = JsonStorage(settings={'state_separator': ':'})
    storage.add_links([
        ('0', ('x',), 'y'),
        ('0', ('y',), 'z'),
        ('1', ('x',), 'y'),
        ('1', ('x',), 'z')
    ])

    fp = StringIO()
    storage.save(fp)
    fp.seek(0)
    loaded = JsonStorage.load(fp)
    assert storage == loaded
