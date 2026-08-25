#
#    Copyright (c) 2026 Manuel Hilgert
#
#    See the file LICENSE for your full rights.
#
"""Drive the whole thing: a real upload in, a loop packet out.

Needs WeeWX installed. Everything below this level is tested without it.
"""

import http.client
import os

import pytest

FIXTURE_PASSKEY = '0000000000000000000000000000AAAA'

weewx = pytest.importorskip('weewx', reason="WeeWX is not installed")

from ecowitt.driver import EcowittDriver  # noqa: E402  (after the skip)


# A WN34 channel goes nowhere until somebody says where. These tests say.
PLACED = {'tf_ch1': 'extraTemp9', 'tf_ch2': 'extraTemp10'}


@pytest.fixture
def driver():
    made = EcowittDriver(port=0, address='127.0.0.1', passkey=FIXTURE_PASSKEY, field_map_extensions=PLACED)
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

    made = EcowittDriver(port=0, address='127.0.0.1', passkey=FIXTURE_PASSKEY, infer_unknown='all',
                         field_map_extensions=PLACED)
    try:
        upload(made, 'PASSKEY=%s&soilmoisture17=30&tempf=59.7' % FIXTURE_PASSKEY)
        packet = next(made.genLoopPackets())
    finally:
        made.closePort()

    assert packet['soilMoist17'] == 30.0
    assert weewx.units.obs_group_dict['soilMoist17'] == 'group_percent'


def test_an_empty_upload_yields_no_packet(driver):
    """Probes and health checks are answered, then ignored."""
    upload(driver, 'PASSKEY=%s&' % FIXTURE_PASSKEY)
    upload(driver, 'PASSKEY=%s&tempf=59.7' % FIXTURE_PASSKEY)

    packet = next(driver.genLoopPackets())
    assert packet['outTemp'] == 59.7


def test_the_hardware_name_is_configurable():
    made = EcowittDriver(port=0, address='127.0.0.1', passkey=FIXTURE_PASSKEY, model='HP2561AE Pro')
    try:
        assert made.hardware_name == 'HP2561AE Pro'
    finally:
        made.closePort()


def test_the_driver_leaves_a_report(tmp_path, payload):
    """Getting a raw upload should not mean reconfiguring the console."""
    path = str(tmp_path / 'report.txt')
    made = EcowittDriver(port=0, address='127.0.0.1', passkey=FIXTURE_PASSKEY, report_file=path)
    try:
        upload(made, payload('hp2561ae_pro'))
        next(made.genLoopPackets())
    finally:
        made.closePort()

    text = open(path, encoding='utf-8').read()
    assert 'PASSKEY=X' in text
    assert 'tempinf=75.4' in text
    assert 'tf_ch1' in text
    assert 'issues/new' in text


def test_the_report_is_written_once(tmp_path, payload):
    path = str(tmp_path / 'report.txt')
    made = EcowittDriver(port=0, address='127.0.0.1', passkey=FIXTURE_PASSKEY, report_file=path)
    try:
        upload(made, payload('hp2561ae_pro'))
        next(made.genLoopPackets())
        first = os.path.getmtime(path)
        upload(made, payload('hp2561ae_pro'))
        next(made.genLoopPackets())
    finally:
        made.closePort()

    assert os.path.getmtime(path) == first


def test_reporting_can_be_switched_off(tmp_path, payload):
    path = str(tmp_path / 'report.txt')
    made = EcowittDriver(port=0, address='127.0.0.1', passkey=FIXTURE_PASSKEY, report_file='')
    try:
        upload(made, payload('hp2561ae_pro'))
        next(made.genLoopPackets())
    finally:
        made.closePort()

    assert not os.path.exists(path)


def test_a_station_with_nothing_unknown_leaves_no_report(tmp_path):
    path = str(tmp_path / 'report.txt')
    made = EcowittDriver(port=0, address='127.0.0.1', passkey=FIXTURE_PASSKEY, report_file=path)
    try:
        upload(made, 'PASSKEY=%s&tempf=59.7&humidity=82' % FIXTURE_PASSKEY)
        next(made.genLoopPackets())
    finally:
        made.closePort()

    assert not os.path.exists(path)
