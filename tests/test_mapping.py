#
#    Copyright (c) 2026 Manuel Hilgert
#
#    See the file LICENSE for your full rights.
#
"""Test the whole way from a captured payload to a WeeWX packet."""

import pytest

from ecowitt.mapping import Mapper


def test_a_real_payload_becomes_a_packet(payload):
    packet, _ = Mapper().to_packet(payload('hp2561ae_pro'))

    assert packet['outTemp'] == 59.7
    assert packet['inTemp'] == 75.4
    assert packet['outHumidity'] == 91.0
    assert packet['barometer'] == 29.920
    assert packet['windSpeed'] == 1.34
    assert packet['radiation'] == 207.36
    assert 'dateTime' in packet


def test_the_sensors_that_the_interceptor_drops(payload):
    """These are the fields an HP2561AE sends that weewx-interceptor throws away."""
    packet, _ = Mapper().to_packet(payload('hp2561ae_pro'))

    assert packet['soilTemp1'] == 66.2          # WN34, first probe
    assert packet['soilTemp2'] == 61.5          # WN34, second probe
    assert packet['soilMoist1'] == 30.0         # WH52
    assert packet['soilmTemp1'] == 65.7         # WH52
    assert packet['lightning_distance'] == 1.0  # WH57
    assert packet['lightning_num'] == 0.0
    assert packet['vpd'] == 0.047


def test_batteries_land_on_the_fields_that_skins_read(payload):
    """A battery on outTempBatteryStatus shows up in a report. On wh65_batt it does not."""
    packet, _ = Mapper().to_packet(payload('hp2561ae_pro'))

    assert packet['outTempBatteryStatus'] == 0.0
    assert packet['lightning_Batt'] == 5.0


def test_identifiers_do_not_reach_the_packet(payload):
    packet, _ = Mapper().to_packet(payload('hp2561ae_pro'))

    for field in ('PASSKEY', 'model', 'stationtype', 'freq', 'heap', 'runtime'):
        assert field not in packet


def test_unknown_fields_are_reported(payload):
    _, guesses = Mapper().to_packet(payload('hp2561ae_pro'))

    assert {g.raw for g in guesses} == {'last24hrainin', 'yearlyrainin'}
    assert all(g.group == 'group_rain' for g in guesses)
    assert not any(g.certain for g in guesses)


def test_a_guess_is_reported_but_not_used(payload):
    """The default keeps a guess out of the database. A wrong unit is worse than a gap."""
    packet, guesses = Mapper().to_packet(payload('hp2561ae_pro'))

    assert guesses
    assert 'ecowitt_yearlyrainin' not in packet


def test_infer_all_takes_the_guess_too(payload):
    packet, _ = Mapper(infer_unknown='all').to_packet(payload('hp2561ae_pro'))

    assert packet['ecowitt_yearlyrainin'] == 0.020


def test_infer_off_reports_nothing_and_takes_nothing(payload):
    packet, guesses = Mapper(infer_unknown='off').to_packet(payload('hp2561ae_pro'))

    assert guesses          # still reported, so the log says what was left out
    assert 'ecowitt_yearlyrainin' not in packet


def test_a_derived_field_is_taken_by_default():
    """A series continued from the catalog is not a guess, so it goes in."""
    packet, guesses = Mapper().to_packet('tf_ch9=66.2')

    assert packet['soilTemp9'] == 66.2
    assert guesses[0].certain is True


def test_extensions_win_over_the_catalog(payload):
    mapper = Mapper(extensions={'yearlyrainin': 'rain_year', 'tempf': 'extraTemp8'})
    packet, guesses = mapper.to_packet(payload('hp2561ae_pro'))

    assert packet['rain_year'] == 0.020
    assert packet['extraTemp8'] == 59.7
    assert 'outTemp' not in packet
    assert {g.raw for g in guesses} == {'last24hrainin'}


def test_a_field_is_only_reported_once(payload):
    mapper = Mapper()
    first = mapper.to_packet(payload('hp2561ae_pro'))[1]
    second = mapper.to_packet(payload('hp2561ae_pro'))[1]

    assert first
    assert second == []


def test_unit_groups_grow_with_what_arrives():
    mapper = Mapper()
    assert 'soilTemp9' not in mapper.wanted_groups()

    mapper.to_packet('tf_ch9=66.2')

    assert mapper.wanted_groups()['soilTemp9'] == 'group_temperature'


def test_bad_mode_is_refused():
    with pytest.raises(ValueError):
        Mapper(infer_unknown='sometimes')


def test_an_empty_payload_yields_only_a_timestamp():
    packet, guesses = Mapper().to_packet('')

    assert list(packet) == ['dateTime']
    assert guesses == []


def test_placement_is_flagged_for_multi_channel_sensors():
    """A WN34 is the same part whether it sits in a bed or a pool."""
    from ecowitt.mapping import placement_note

    assert placement_note('tf_ch9')
    assert placement_note('temp1f')
    assert placement_note('leafwetness_ch3')
    # The single outdoor sensor is not a channel, and not in question.
    assert placement_note('tempf') is None
    assert placement_note('humidity') is None


def test_a_channel_can_be_put_where_it_actually_is():
    """The pool lead reports as tf_ch2. It is not a soil temperature."""
    mapper = Mapper(extensions={'tf_ch2': 'extraTemp5'})
    packet, _ = mapper.to_packet('tf_ch1=66.2&tf_ch2=78.4')

    assert packet['soilTemp1'] == 66.2
    assert packet['extraTemp5'] == 78.4
    assert 'soilTemp2' not in packet


def test_a_derived_channel_can_be_redirected_too():
    """What holds for the catalog holds for a channel the driver worked out."""
    mapper = Mapper(extensions={'tf_ch9': 'extraTemp6'})
    packet, guesses = mapper.to_packet('tf_ch9=78.4')

    assert packet['extraTemp6'] == 78.4
    assert guesses == []
