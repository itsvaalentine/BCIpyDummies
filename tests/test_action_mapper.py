from bcipydummies.control.action_mapper import ActionMapper


def test_actionmapper_left():
    assert ActionMapper.map("left") == "A"


def test_actionmapper_right():
    assert ActionMapper.map("right") == "D"


def test_actionmapper_lift():
    assert ActionMapper.map("lift") == "SPACE"


def test_actionmapper_invalid_action():
    assert ActionMapper.map("unknown") is None
