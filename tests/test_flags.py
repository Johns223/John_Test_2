from shipping import flags


def test_a_flag_defaults_to_off():
    assert flags.is_enabled("new_rate_engine") is False


def test_a_flag_defaults_to_on():
    assert flags.is_enabled("strict_customs_validation") is True


def test_enabling_a_flag():
    flags.enable("async_notifications")
    assert flags.is_enabled("async_notifications") is True


def test_disabling_a_flag():
    flags.disable("strict_customs_validation")
    assert flags.is_enabled("strict_customs_validation") is False


def test_an_unknown_flag_is_off():
    assert flags.is_enabled("no_such_flag") is False
