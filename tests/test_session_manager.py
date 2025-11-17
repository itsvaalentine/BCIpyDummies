import pytest
from bcipydummies.cortex.session_manager import SessionManager


def test_sessionmanager_initial_state():
    sm = SessionManager()
    assert sm.cortex_token is None
    assert sm.session_id is None
    assert sm.headset_id is None


def test_sessionmanager_set_token():
    sm = SessionManager()
    sm.set_token("ABC123")
    assert sm.cortex_token == "ABC123"


def test_sessionmanager_set_headset():
    sm = SessionManager()
    sm.set_headset("HEADSET1")
    assert sm.headset_id == "HEADSET1"


def test_sessionmanager_set_session():
    sm = SessionManager()
    sm.set_session("SESSION1")
    assert sm.session_id == "SESSION1"
