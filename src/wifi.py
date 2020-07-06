"""Testing file."""
from .hostapd import HostAP
from .dnsmasq import DNSMasq
from .network_interface import NetworkInterface
from .wificommon import WiFi
import subprocess
import os
import signal
import asyncio
from netifaces import ifaddresses, AF_INET


class WiFiHandler(WiFi):
    """Handles WiFi interface."""

    def __init__(self, interface, internet_interface,
                 wifi_ap_password,
                 tshark_bin='/usr/bin/tshark'):
        """Initialize WiFi handler."""
        super(WiFiHandler, self).__init__(interface)
        self.interface = interface
        self.internet_interface = internet_interface
        self.hotspot = HostAP(self.interface, self.wifi_ap_password=self.wifi_ap_password)
        self.dns_server = DNSMasq(self.interface, self.internet_interface)
        self.network_interface = NetworkInterface(self.interface)
        self.data_collector_process = None
        self.loop = None
        self.tshark_bin = tshark_bin

    def init_wifi(self):
        """Initialize wifi."""
        self.network_interface.init_network()

    def set_hostap_mode(self):
        """Set network interface host ap mode."""
        self.network_interface.set_hostap_mode()
        self.hotspot.start()
        self.dns_server.start()

    def change_hostap(self, ssid, channel):
        """Change host access point."""
        self.hotspot.set_hostap_ssid(ssid)
        self.hotspot.set_hostap_channel(channel)
        self.hotspot.set_hostap_conf()
        self.hotspot.restart()

    def stop_hostap(self):
        """Stop host access point."""
        self.hotspot.stop()
        self.dns_server.stop()

    def set_hostap_optout(self, mac_list):
        """Set optout mac addresses for hostap."""
        self.hotspot.deny_mac(mac_list)

    def set_probe_req_mode(self):
        """Set network interface in probe req mode."""
        self.network_interface.set_probe_req_mode()

    def start_collecting_data(
            self, output, probe_req_only=True,
            time_interval_channel=10):
        """Start collecting data."""
        tshark_cmd = '{} -i {} -w {}'.format(
            self.tshark_bin, self.interface, output)
        if probe_req_only:
            self.loop = asyncio.get_event_loop()
            self.loop.run_in_executor(
                None, self.network_interface.circular_channel_switching,
                time_interval_channel)
            tshark_cmd += ' -f "wlan subtype probereq"'
        self.data_collector_process = subprocess.Popen(
            tshark_cmd, shell=True, preexec_fn=os.setpgrp,
            stdout=subprocess.PIPE)

    def stop_collecting_data(self):
        """Stop collecting data."""
        if self.loop:
            self.loop.stop()
            self.loop = None
        if self.data_collector_process:
            os.killpg(
                os.getpgid(
                    self.data_collector_process.pid),
                signal.SIGTERM)
        self.data_collector_process = None

    def get_connected_users(self):
        """Get mac addresses of connected users in a list."""
        return self.hotspot.get_connected_users_advanced()

    def get_external_ip(self):
        """Get external IP address of pi."""
        try:
            return ifaddresses(self.internet_interface)[AF_INET][0]['addr']
        except KeyError:
            return "127.0.0.1"
