"""
Tests for pi_sniffer
"""
import tempfile
from unittest.mock import MagicMock, patch, ANY
import sys

sys.modules["sysdmanager"] = MagicMock()
from pi_sniffer import PiSniffer, WiFiState

INT_IFACE = "wlan0"
EXT_IFACE = "wlan1"
AUTH_CODE = "generatedAuthCode"
SERVER_URL = "http://localhost:8000"
WIFI_AP_PASSWORD = "123456789"


# def mock_pi_sniffer():
#     mock_sniffer = MagicMock()
#     print("HEHAUDHSD")
#
#     mock_sniffer.wifi.return_value = MagicMock()
#     mock_sniffer.mac.return_value = "MY MAC"
#     mock_sniffer.ip.return_value = "1.2.3.4"
#
#     mock_sniffer.state = WiFiState.NoState
#     mock_sniffer.status_update_interval.return_value = 5
#
#     mock_sniffer.server_url = SERVER_URL
#     mock_sniffer.is_instruction_available.return_value = None
#     mock_sniffer.session_id.return_value = None
#     mock_sniffer.data_file.return_value = None
#     mock_sniffer.access_point.return_value = dict(channel=None, ssid=None, sticky_ap=0)
#
#     mock_sniffer.req_session.return_value = MagicMock()
#     mock_sniffer.observer.return_value = None
#
#     for func in PiSniffer.__dict__.keys():
#         print(func)
#         if not str(func).startswith("__"):
#             mock_sniffer.func.return_value = MagicMock()
#     return mock_sniffer


def mock_init(self, ext_iface, int_iface, wifi_ap_password, token, server_url):
    self.wifi = MagicMock()
    self.mac = "MY MAC"
    self.ip = "1.2.3.4"

    self.state = WiFiState.NoState
    self.status_update_interval = 5

    self.server_url = SERVER_URL
    self.is_instruction_available = None
    self.session_id = 1
    self.data_file = None
    self.access_point = dict(channel=None, ssid=None, sticky_ap=0)

    self.req_session = MagicMock()
    get = MagicMock()
    get.json.return_value = {"ssid": "MY SSID", "channel": 42}
    self.req_session.get.return_value = get

    self.observer = MagicMock()
    self._create_urls()


@patch.object(PiSniffer, "__init__", mock_init)
def test_start_probe_request_mode_and_capturing_data():
    mock_sniffer = PiSniffer(None, None, None, None, None)
    mock_sniffer.execute_instruction(1)
    mock_sniffer.wifi.set_probe_req_mode.assert_called_once()
    mock_sniffer.wifi.start_collecting_data.assert_called_once_with(
        mock_sniffer.data_file, probe_req_only=True
    )

    # Second execution of instruction 1 should NOT call the function again as collection has been started
    mock_sniffer.execute_instruction(1)
    mock_sniffer.wifi.set_probe_req_mode.assert_called_once()
    mock_sniffer.wifi.start_collecting_data.assert_called_once_with(
        mock_sniffer.data_file, probe_req_only=True
    )


@patch.object(PiSniffer, "__init__", mock_init)
def test_stop_probe_request_mode_and_send_data():
    mock_sniffer = PiSniffer(None, None, None, None, None)
    mock_sniffer.execute_instruction(2)
    mock_sniffer.wifi.stop_collecting_data.assert_not_called()

    # Start probe request mode and capturing
    mock_sniffer.execute_instruction(1)

    # Now we expect data collection to be stopped and data to be sent
    with tempfile.NamedTemporaryFile(suffix=".pcapng") as data_file:
        mock_sniffer.data_file = data_file.name

        mock_sniffer.execute_instruction(2)
        mock_sniffer.wifi.stop_collecting_data.assert_called_once()
        mock_sniffer.req_session.post.assert_called_once_with(
            "http://localhost:8000/probe/analyze/",
            data={
                "mac": "MY MAC",
                "name": data_file.name,
                "session_id": 1,
            },
            files={
                "data": ANY
            },  # Had to use ANY here as the two BufferedReaders were causing an Assertion Error.
        )


@patch.object(PiSniffer, "__init__", mock_init)
@patch("pi_sniffer.DumpcapObserver", autospec=True)
def test_start_hotspot_mode_and_capturing_data(mock_observer):
    mock_sniffer = PiSniffer(None, None, None, None, None)
    mock_sniffer.execute_instruction(3)

    # Assert ap is started
    mock_sniffer.wifi.set_hostap_mode.assert_called_once()
    mock_sniffer.req_session.get.assert_called_once_with(
        "http://localhost:8000/session/ap/", params={"sticky": 0}
    )
    mock_sniffer.wifi.change_hostap.assert_called_once_with("MY SSID", 42)

    # Assert data collection is started and observer is created
    mock_sniffer.wifi.start_collecting_ap_data(mock_sniffer.data_file)
    mock_observer.assert_called_once_with(
        mock_sniffer.req_session,
        1,
        "MY MAC",
        "http://localhost:8000/ap/analyze/",
        path="/tmp/pi_sniffer_data",
    )


@patch.object(PiSniffer, "__init__", mock_init)
def test_stop_hotspot_mode_and_send_data():
    mock_sniffer = PiSniffer(None, None, None, None, None)
    mock_sniffer.execute_instruction(4)

    # Expect no calls as hotspot has not yet been started
    mock_sniffer.wifi.stop_collecting_ap_data.assert_not_called()
    mock_sniffer.observer.shutdown_observer.assert_not_called()

    # Start hotspot and expect the correct calls when stopping it
    with patch("pi_sniffer.DumpcapObserver", autospec=True):
        mock_sniffer.execute_instruction(3)
        mock_sniffer.execute_instruction(4)
        mock_sniffer.wifi.stop_collecting_ap_data.assert_called_once()
        mock_sniffer.observer.shutdown_observer.assert_called_once()


@patch.object(PiSniffer, "__init__", mock_init)
def test_stop_everything():
    mock_sniffer = PiSniffer(None, None, None, None, None)
    mock_sniffer.execute_instruction(5)

    # Expect no calls as Probe requests neither hostspot has been started
    mock_sniffer.wifi.stop_collecting_ap_data.assert_not_called()
    mock_sniffer.wifi.stop_collecting_data.assert_not_called()

    # Test stopping of Probe request mode.
    with patch("pi_sniffer.open"):
        mock_sniffer.execute_instruction(1)
        mock_sniffer.execute_instruction(5)
        mock_sniffer.wifi.stop_collecting_data.assert_called_once()
        mock_sniffer.req_session.post.assert_called_once()

    # Test stopping of HostAP request mode.
    with patch("pi_sniffer.DumpcapObserver", autospec=True):
        mock_sniffer.execute_instruction(3)
        mock_sniffer.execute_instruction(5)
        mock_sniffer.wifi.restart_opennds.assert_called_once()
        mock_sniffer.wifi.stop_collecting_ap_data.assert_called_once()
        mock_sniffer.observer.shutdown_observer.assert_called_once()


@patch.object(PiSniffer, "__init__", mock_init)
@patch("pi_sniffer.DumpcapObserver", autospec=True)
def test_start_sticky_hotspot_mode_and_start_capturing(mock_observer):
    mock_sniffer = PiSniffer(None, None, None, None, None)
    mock_sniffer.execute_instruction(6)

    # Assert ap is started
    mock_sniffer.wifi.set_hostap_mode.assert_called_once()
    mock_sniffer.req_session.get.assert_called_once_with(
        "http://localhost:8000/session/ap/", params={"sticky": 1}
    )
    mock_sniffer.wifi.change_hostap.assert_called_once_with("MY SSID", 42)

    # Assert data collection is started and observer is created
    mock_sniffer.wifi.start_collecting_ap_data(mock_sniffer.data_file)
    mock_observer.assert_called_once_with(
        mock_sniffer.req_session,
        1,
        "MY MAC",
        "http://localhost:8000/ap/analyze/",
        path="/tmp/pi_sniffer_data",
    )


@patch.object(PiSniffer, "__init__", mock_init)
def test_start_and_stop_probe_request_mode_during_hotspot_mode_no_effect():
    mock_sniffer = PiSniffer(None, None, None, None, None)
    with patch("pi_sniffer.DumpcapObserver", autospec=True):
        mock_sniffer.execute_instruction(3)

    # Starting or stopping hotspot mode should have no effect here as we are in probe request mode.
    mock_sniffer.execute_instruction(1)
    mock_sniffer.wifi.set_probe_req_mode.assert_not_called()
    mock_sniffer.wifi.start_collecting_data.assert_not_called()

    mock_sniffer.execute_instruction(2)
    mock_sniffer.wifi.stop_collecting_data.assert_not_called()


@patch.object(PiSniffer, "__init__", mock_init)
def test_start_and_stop_hotspot_mode_during_probe_request_mode_no_effect():
    mock_sniffer = PiSniffer(None, None, None, None, None)
    mock_sniffer.execute_instruction(1)

    # Starting or stopping probe request mode should have no effect here as we are in hotspot mode.
    mock_sniffer.execute_instruction(3)
    mock_sniffer.execute_instruction(6)
    mock_sniffer.wifi.set_hostap_mode.assert_not_called()
    mock_sniffer.wifi.change_hostap.assert_not_called()
    mock_sniffer.wifi.start_collecting_ap_data.assert_not_called()

    mock_sniffer.execute_instruction(4)
    mock_sniffer.wifi.stop_collecting_ap_data.assert_not_called()
    mock_sniffer.observer.shutdown_observer.assert_not_called()
