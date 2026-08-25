#
#    Copyright (c) 2026 Manuel Hilgert
#
#    See the file LICENSE for your full rights.
#
"""Test the protocol parser against captured payloads."""

import calendar
import time

from ecowitt import protocol


def test_parses_a_real_payload(payload):
    raw = protocol.parse(payload('hp2561ae_pro'))

    assert len(raw) == 45
    assert raw['model'] == 'HP2561AE_Pro_V2.1.4'
    assert raw['tempf'] == '59.7'
    # A plus sign in a value is a space, and the parser has to know that.
    assert raw['dateutc'] == '2026-08-25 11:06:42'


def test_a_wunderground_query_parses_the_same_way():
    """The two protocols differ in how they travel, not in what they carry."""
    raw = protocol.parse('?ID=KX&PASSWORD=y&tempf=61.0&humidity=82&action=updateraw')

    assert raw['tempf'] == '61.0'
    assert raw['humidity'] == '82'


def test_empty_payload():
    assert protocol.parse('') == {}
    assert protocol.parse(None) == {}


def test_numbers_are_separated_from_identifiers(payload):
    raw = protocol.parse(payload('hp2561ae_pro'))
    readings, text = protocol.numbers(raw)

    assert readings['tempf'] == 59.7
    assert readings['tf_ch1'] == 66.2
    assert 'PASSKEY' not in readings
    assert text['model'] == 'HP2561AE_Pro_V2.1.4'
    # Metadata that happens to be numeric is still metadata.
    assert 'heap' not in readings
    assert text['heap'] == '22764'


def test_a_missing_reading_stays_as_a_gap():
    """A sensor that has nothing to say is a fact, not a reason to drop the field."""
    readings, _ = protocol.numbers({'tempf': '', 'humidity': '--', 'tf_ch1': '66.2'})

    assert readings == {'tempf': None, 'humidity': None, 'tf_ch1': 66.2}


def test_unreadable_value_is_kept_as_text():
    readings, text = protocol.numbers({'tempf': 'warm'})

    assert readings == {}
    assert text == {'tempf': 'warm'}


def test_device_time_is_used_when_it_is_plausible(payload):
    raw = protocol.parse(payload('hp2561ae_pro'))
    sent = calendar.timegm(time.strptime('2026-08-25 11:06:42', '%Y-%m-%d %H:%M:%S'))

    assert protocol.device_time(raw, now=sent + 30) == sent


def test_device_time_is_refused_when_it_is_not(payload):
    """Consoles are often wrong about the time, sometimes by years."""
    raw = protocol.parse(payload('hp2561ae_pro'))
    a_year_later = calendar.timegm(time.strptime('2027-08-25 11:06:42',
                                                 '%Y-%m-%d %H:%M:%S'))

    assert protocol.device_time(raw, now=a_year_later) is None


def test_device_time_survives_nonsense():
    assert protocol.device_time({'dateutc': 'now'}) is None
    assert protocol.device_time({'dateutc': 'yesterday'}) is None
    assert protocol.device_time({}) is None
