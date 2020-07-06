"""Wifi Sniffer.

- 0: Shut down all the updates and exit.
- 1: Start probe request mode and start capturing data.
- 2: Stop probe request mode and send captured data.
- 3: Start hotspot mode and start capturing data.
- 4: Stop hotspot mode and send captured data.
- 5: Stop whatever is going on
- 6: Start sticky hotspot mode and start capturing data.
"""
from src.wifi import WiFiHandler
import time
import requests
import enum
import urllib
import threading
import datetime
import os
import json
import configargparse


parser = configargparse.ArgumentParser(description='Start pi data collector.')
parser.add_argument('-c', '--config', required=True, is_config_file=True,
                    help='Config file path', default='config.ini')
parser.add_argument('--int_iface', required=True,
                    help='Internal WiFi interface.')
parser.add_argument('--ext_iface', required=True,
                    help='External WiFi interface.')
parser.add_argument('--auth_code', required=True, help='Authentication code.')
parser.add_argument('--server_url', required=True, help='Server URL.')


class WiFiState(enum.Enum):
    """WiFi state enum."""

    NoState = 0
    ProbeReq = 1
    HostAP = 2


class PiSniffer(object):
    """Pi sniffer class."""

    def __init__(self, ext_iface, int_iface, wifi_ap_password, token, server_url):
        """Initialize pi sniffer object."""
        self.wifi = WiFiHandler(ext_iface, int_iface, wifi_ap_password)
        self.mac = self.wifi.get_device_mac()
        self.ip = self.wifi.get_external_ip()
        self.state = WiFiState.NoState
        self.status_update_interval = 5
        self.server_url = server_url
        self.is_instruction_available = None
        self.session_id = None
        self.data_file = None
        self.access_point = dict(
            channel=None,
            ssid=None,
            sticky_ap=0)
        self.req_session = requests.Session()
        self.req_session.headers.update({'token': token})

        self._create_urls()
        self.set_wifi_state()
        self.start_updates()
        self.fetch_and_execute_instructions()

    def _create_urls(self):
        """Create URLs during initialization."""
        self.urls = dict(
            status_update=urllib.parse.urljoin(
                self.server_url, 'status/update/'),
            instruction_fetch=urllib.parse.urljoin(
                self.server_url, 'instructions/get_for_execution/'),
            executed=urllib.parse.urljoin(
                self.server_url, 'instructions/executed/'),
            probe=urllib.parse.urljoin(
                self.server_url, 'probe/analyze/'),
            session_fetch=urllib.parse.urljoin(
                self.server_url, 'session/latest/'),
            ap_analyze=urllib.parse.urljoin(
                self.server_url, 'ap/analyze/'),
            ap_fetch=urllib.parse.urljoin(
                self.server_url, 'session/ap/'),
            opted_out_mac=urllib.parse.urljoin(
                self.server_url, 'ap/optout/')
        )

    def set_wifi_state(self, mode=None):
        """Set wifi state as per state of object."""
        self.state = mode if mode else self.state
        if self.state == WiFiState.HostAP:
            self.wifi.set_hostap_mode()
        else:
            self.wifi.set_probe_req_mode()

    def send_status_update(self):
        """Send regular status update."""
        while True:
            connected_users = self.wifi.get_connected_users() if \
                self.state == WiFiState.HostAP else None
            ap_details = {
                'access_point': self.access_point,
                'connected_users': connected_users
            }
            payload = {
                'mac': self.mac,
                'ip': self.ip,
                'state': str(self.state),
                'ap_details': ap_details}
            print(json.dumps(payload))
            try:
                response = self.req_session.post(
                    self.urls['status_update'],
                    data=json.dumps(payload), timeout=20).json()
                print(response)
                self.is_instruction_available = \
                    response['is_instruction_available']
            except Exception as e:
                print(e)
            time.sleep(self.status_update_interval)

    def start_updates(self):
        """Start status updates in a thread."""
        self.status_update_thread = threading.Thread(
            target=self.send_status_update, args=())
        self.status_update_thread.daemon = True   # Daemonize thread
        self.status_update_thread.start()  # Start the execution

    def fetch_and_execute_instructions(self):
        """Fetch and run instruction if available."""
        while(True):
            if self.is_instruction_available:
                instruction = self.fetch_instruction()
                self.fetch_and_set_session_id()
                if self.session_id:
                    self.execute_instruction(instruction)
                else:
                    self.execute_instruction(5)
                self.req_session.post(
                    self.urls['executed'], data={
                        'mac': self.mac,
                        'code': instruction})
                self.is_instruction_available = 0
            else:
                time.sleep(self.status_update_interval // 2)

    def fetch_instruction(self):
        """Fetch instructions for the pi."""
        response = self.req_session.get(
            self.urls['instruction_fetch'], params={'mac': self.mac}).json()
        return int(response['code'])

    def fetch_and_set_session_id(self):
        """Fetch and set session id."""
        resp = self.req_session.get(self.urls['session_fetch']).json()
        if resp['id'] != 0:
            self.session_id = resp['id']
        else:
            self.session_id = None

    def fetch_and_set_ap(self, sticky_ap):
        """Fetch and set access point."""
        ap = self.req_session.get(
            self.urls['ap_fetch'], params={'sticky': sticky_ap}).json()
        self.set_access_point(ap['ssid'], ap['channel'], sticky_ap)

    def set_optout_mac(self):
        """Fetch and set optout mac."""
        mac_list = self.req_session.get(self.urls['opted_out_mac']).json()
        mac_list = mac_list['mac']
        self.wifi.set_hostap_optout(mac_list)

    def execute_instruction(self, code):
        """Execute instructions for the pi."""
        if code == 1 and self.state == WiFiState.NoState:
            self.start_collecting_probe()
        elif code == 2 and self.state == WiFiState.ProbeReq:
            self.stop_collecting_probe()
        elif code in [3, 6]:
            start = True
            if self.state == WiFiState.HostAP and self.data_file:
                self.stop_collecting_ap(change_state=False)
            elif self.state == WiFiState.NoState:
                self.set_optout_mac()
                self.set_wifi_state(WiFiState.HostAP)
            else:
                start = False
            if start:
                sticky_ap = 1 if code == 6 else 0
                self.fetch_and_set_ap(sticky_ap)
                self.start_collecting_ap()
        elif code == 4 and self.state == WiFiState.HostAP:
            self.stop_collecting_ap()
        elif code == 5:
            if self.state == WiFiState.HostAP:
                self.execute_instruction(4)
            elif self.state == WiFiState.ProbeReq:
                self.execute_instruction(2)

    def start_collecting_probe(self):
        """Start collecting probe request data."""
        self.set_wifi_state(WiFiState.ProbeReq)
        self.data_file = '{}_{}_probe.pcapng'.format(
            self.session_id, datetime.datetime.now().strftime(
                '%d%m%Y%H%M%S'))
        self.wifi.start_collecting_data(
            self.data_file, probe_req_only=True)

    def stop_collecting_probe(self):
        """Stop collecting probe request data and send."""
        self.wifi.stop_collecting_data()
        self.set_wifi_state(WiFiState.NoState)
        response = self.req_session.post(
            self.urls['probe'], data={
                'mac': self.mac, 'name': self.data_file,
                'session_id': self.session_id},
            files={'data': open(self.data_file, 'rb')})
        if response.status_code == 200:
            os.remove(self.data_file)
            self.data_file = None

    def set_access_point(self, ssid, channel, sticky_ap):
        """Set access point for the pi."""
        self.access_point['channel'] = channel
        self.access_point['ssid'] = ssid
        self.access_point['sticky_ap'] = sticky_ap
        self.wifi.change_hostap(
            self.access_point['ssid'], self.access_point['channel'])

    def start_collecting_ap(self):
        """Start collecting access point data."""
        self.data_file = '{}_{}_ap.pcapng'.format(
            self.session_id, datetime.datetime.now().strftime(
                '%d%m%Y%H%M%S'))
        self.wifi.start_collecting_data(
            self.data_file, probe_req_only=False)

    def stop_collecting_ap(self, change_state=True):
        """Stop collecting access point data."""
        self.wifi.stop_collecting_data()
        if change_state:
            self.set_wifi_state(WiFiState.NoState)
        response = self.req_session.post(
            self.urls['ap_analyze'], data={
                'mac': self.mac, 'name': self.data_file,
                'session_id': self.session_id},
            files={'data': open(self.data_file, 'rb')})
        if response.status_code == 200:
            os.remove(self.data_file)
            self.data_file = None


if __name__ == '__main__':
    args = parser.parse_args()
    while True:
        try:
            pi_sniffer = PiSniffer(
                args.ext_iface, args.int_iface, args.wifi_ap_password, 
                args.auth_code, args.server_url)
        except Exception as e:
            # ToDo: print exception
            pass
