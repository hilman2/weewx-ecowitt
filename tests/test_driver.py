#
#    Copyright (c) 2026 Manuel Hilgert
#
#    See the file LICENSE for your full rights.
#
"""Drive the whole thing: a real upload in, a loop packet out.

Needs WeeWX installed. Everything below this level is tested without it.
"""

import http.client

import pytest

weewx = pytest.importorskip('weewx', reason="WeeWX is not installed")

from ecowitt.driver import EcowittDriver  # noqa: E402  (after the skip)


# A WN34 channel goes nowhere until somebody says where. These tests say.
PLACED = {'tf_ch1': 'extraTemp9', 'tf_ch2': 'extraTemp10'}


@pytest.fixture
def driver():
    made = EcowittDriver(port=0, address='127.0.0.1', field_map_extensions=PLACED)
    yield made
    made.closePort()


def upload(driver, body):
    connection = http.client.HTTPConnection('127.0.0.1', driver.listener.port, timeout=5)
    try:
        connection.request('POST', '/', body)
        response = connection.getresponse()
        return response.status, response.read()
    finally:
        connection.close()


def test_an_upload_becomes_a_loop_packet(driver, payload):
    status, answer = upload(driver, payload('hp2561ae_pro'))

    assert status == 200
    # The gateway counts the upload as failed until it has read this.
    assert answer == b'{"errcode":"0","errmsg":"ok"}'

    packet = next(driver.genLoopPackets())
    assert packet['usUnits'] == weewx.US
    assert packet['outTemp'] == 59.7
    assert packet['extraTemp9'] == 66.2
    assert packet['lightning_distance'] == 1.0
    assert packet['dateTime'] > 0


def test_new_fields_reach_the_unit_system(payload):
    """A new field is no use in a report if WeeWX does not know what it is.

    A seventeenth soil channel is past what Ecowitt publishes, so it takes
    infer_unknown = all. Which is exactly when somebody would set that.
    """
    import weewx.units

    made = EcowittDriver(port=0, address='127.0.0.1', infer_unknown='all',
                         field_map_extensions=PLACED)
    try:
        upload(made, 'soilmoisture17=30&tempf=59.7')
        packet = next(made.genLoopPackets())
    finally:
        made.closePort()

    assert packet['soilMoist17'] == 30.0
    assert weewx.units.obs_group_dict['soilMoist17'] == 'group_percent'


def test_an_empty_upload_yields_no_packet(driver):
    """Probes and health checks are answered, then ignored."""
    upload(driver, '')
    upload(driver, 'tempf=59.7')

    packet = next(driver.genLoopPackets())
    assert packet['outTemp'] == 59.7


def test_the_hardware_name_is_configurable():
    made = EcowittDriver(port=0, address='127.0.0.1', model='HP2561AE Pro')
    try:
        assert made.hardware_name == 'HP2561AE Pro'
    finally:
        made.closePort()
