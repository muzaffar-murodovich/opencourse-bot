import config


def test_parse_ids_basic():
    assert config._parse_ids("1, 2,3") == {1, 2, 3}


def test_parse_ids_empty():
    assert config._parse_ids("") == set()
    assert config._parse_ids("   ") == set()
