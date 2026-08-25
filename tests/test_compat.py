#
#    Copyright (c) 2026 Manuel Hilgert
#
#    See the file LICENSE for your full rights.
#
"""Test that a history started under another driver carries on."""

import pytest

from ecowitt import compat
from ecowitt.mapping import Mapper


def test_no_profile_by_default():
    assert compat.profile(None) == {}
    assert compat.profile('none') == {}


def test_an_unknown_profile_is_refused():
    with pytest.raises(ValueError):
        compat.profile('whatever')


def test_coming_from_ecowittcustom_keeps_its_fields(payload):
    """That driver put the WN34 on soilTemp. Somebody's history says so."""
    packet, _ = Mapper(compat_with='ecowittcustom').to_packet(payload('hp2561ae_pro'))

    assert packet['soilTemp1'] == 66.2       # tf_ch1, as it always was
    assert packet['soilTemp2'] == 61.5
    assert packet['soilmTemp1'] == 65.7      # the WH52, back where it was
    assert 'extraTemp9' not in packet


def test_the_default_is_the_other_way_round(payload):
    """A fresh install gets the placement that matches the hardware."""
    packet, _ = Mapper().to_packet(payload('hp2561ae_pro'))

    assert packet['extraTemp9'] == 66.2
    assert packet['soilTemp1'] == 65.7       # the WH52, which really is in the ground


def test_the_wn34_does_not_land_on_the_wh52(payload):
    """The point of the profile: two sensors must not share one column."""
    packet, _ = Mapper(compat_with='ecowittcustom').to_packet(payload('hp2561ae_pro'))

    assert packet['soilTemp1'] != packet['soilmTemp1']


def test_your_own_mapping_still_wins(payload):
    mapper = Mapper(compat_with='ecowittcustom',
                    extensions={'tf_ch1': 'extraTemp5'})
    packet, _ = mapper.to_packet(payload('hp2561ae_pro'))

    assert packet['extraTemp5'] == 66.2
    assert 'soilTemp1' not in packet or packet.get('soilTemp1') != 66.2


def test_the_gateway_profile_agrees_with_our_default(payload):
    """Nobody arriving from there needs anything, but saying so must not break."""
    theirs, _ = Mapper(compat_with='gw1000').to_packet(payload('hp2561ae_pro'))
    ours, _ = Mapper().to_packet(payload('hp2561ae_pro'))

    assert theirs['extraTemp9'] == ours['extraTemp9']
