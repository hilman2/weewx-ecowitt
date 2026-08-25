#
#    Copyright (c) 2026 Manuel Hilgert
#
#    See the file LICENSE for your full rights.
#
"""Several consoles, one WeeWX.

Ecowitt users add a second gateway to reach sensors the first one cannot hear. Both
number their channels from one, so a WN34 on channel 1 of each would land in the same
field and overwrite the other. The PASSKEY in every upload says which console sent it.
"""

import http.client

import pytest

weewx = pytest.importorskip('weewx', reason="WeeWX is not installed")

from ecowitt.driver import EcowittDriver             # noqa: E402
from ecowitt.protocol import station_id              # noqa: E402

GARDEN = 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
ROOF = 'BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB'

TWO_CONSOLES = {
    'garden': {'passkey': GARDEN,
               'field_map_extensions': {'tf_ch1': 'soilTemp1'}},
    'roof': {'passkey': ROOF,
             'field_map_extensions': {'tf_ch1': 'extraTemp12'}},
}


@pytest.fixture
def driver():
    made = EcowittDriver(port=0, address='127.0.0.1', report_file='',
                         stations=TWO_CONSOLES)
    yield made
    made.closePort()


def post(driver, body):
    connection = http.client.HTTPConnection('127.0.0.1', driver.listener.port, timeout=5)
    try:
        connection.request('POST', '/', body)
        connection.getresponse().read()
    finally:
        connection.close()


def test_the_passkey_is_read_without_parsing_everything():
    assert station_id('PASSKEY=ABC&tempf=59.7') == 'ABC'
    assert station_id('tempf=59.7') is None
    assert station_id('') is None


def test_each_console_keeps_its_own_channels(driver):
    """Channel 1 of one console is not channel 1 of the other."""
    post(driver, 'PASSKEY=%s&tf_ch1=66.0' % GARDEN)
    post(driver, 'PASSKEY=%s&tf_ch1=41.2' % ROOF)

    packets = driver.genLoopPackets()
    first, second = next(packets), next(packets)
    readings = {p['station']: p for p in (first, second)}

    assert readings['garden']['soilTemp1'] == 66.0
    assert readings['roof']['extraTemp12'] == 41.2
    assert 'extraTemp12' not in readings['garden']
    assert 'soilTemp1' not in readings['roof']


def test_the_packet_says_which_console_it_came_from(driver):
    post(driver, 'PASSKEY=%s&tempf=59.7' % GARDEN)

    assert next(driver.genLoopPackets())['station'] == 'garden'


def test_an_unknown_console_is_ignored_and_named(driver, caplog):
    import logging

    with caplog.at_level(logging.WARNING):
        post(driver, 'PASSKEY=CCCC&tempf=59.7')
    post(driver, 'PASSKEY=%s&tempf=61.0' % GARDEN)

    assert next(driver.genLoopPackets())['outTemp'] == 61.0
    assert 'CCCC' in caplog.text
    assert '[[stations]]' in caplog.text


def test_an_unknown_console_is_named_once(driver, caplog):
    """The warning belongs to the moment the upload is read, and once is enough."""
    import logging

    packets = driver.genLoopPackets()
    with caplog.at_level(logging.WARNING):
        post(driver, 'PASSKEY=CCCC&tempf=59.7')
        post(driver, 'PASSKEY=%s&tempf=61.0' % GARDEN)
        next(packets)
        assert 'CCCC' in caplog.text

        caplog.clear()
        post(driver, 'PASSKEY=CCCC&tempf=59.8')
        post(driver, 'PASSKEY=%s&tempf=62.0' % GARDEN)
        assert next(packets)['outTemp'] == 62.0

    assert caplog.text == ''


def test_one_console_needs_no_stations_section():
    """Nothing changes for the ordinary case."""
    made = EcowittDriver(port=0, address='127.0.0.1', report_file='',
                         field_map_extensions={'tf_ch1': 'extraTemp9'})
    try:
        post(made, 'PASSKEY=whatever&tf_ch1=66.0&tempf=59.7')
        packet = next(made.genLoopPackets())
    finally:
        made.closePort()

    assert packet['extraTemp9'] == 66.0
    assert 'station' not in packet


def test_a_station_without_a_passkey_is_refused():
    with pytest.raises(ValueError):
        EcowittDriver(port=0, address='127.0.0.1',
                      stations={'garden': {'field_map_extensions': {}}})
