"""Testing file."""

import asyncio
import dbus
import os
import subprocess
import signal
from netifaces import ifaddresses, AF_INET  # pylint: disable=no-name-in-module
from .hostapd import HostAP
from .dnsmasq import DNSMasq
from .network_interface import NetworkInterface
from .wificommon import WiFi


class WiFiHandler(WiFi):  # pylint: disable=too-many-instance-attributes
    """Handles WiFi interface."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        ext_iface,
        int_iface,
        wifi_ap_password,
        tshark_bin="/usr/bin/tshark",
        dumpcap_bin="dumpcap",
        dumpcap_file_generation_duration=15,
    ):
        """Initialize WiFi handler."""

        super(WiFiHandler, self).__init__(ext_iface)
        self.ext_iface = ext_iface
        self.int_iface = int_iface
        self.hotspot = HostAP(self.ext_iface, wifi_ap_password=wifi_ap_password)
        self.dns_server = DNSMasq(self.ext_iface, self.int_iface)
        self.network_interface = NetworkInterface(self.ext_iface)
        self.data_collector_process = None
        self.ap_data_collector_process = None
        self.loop = None
        self.dumpcap_bin = dumpcap_bin
        self.dumpcap_file_generation_duration = dumpcap_file_generation_duration
        self.tshark_bin = tshark_bin

    def init_wifi(self):
        """Initialize wifi."""
        self.network_interface.init_network()

    def restart_opennds(self):
        """Restart opennds so authenticated devices are forgotten."""
        print("restarting opennds")
        self.execute_command("systemctl restart opennds.service")

    def set_hostap_mode(self):
        """Set network interface host ap mode."""
        self.network_interface.set_hostap_mode()
        self.hotspot.start()
        self.dns_server.start()

    def change_hostap(self, ssid, channel):
        """Change host access point."""
        print(f"Hostap ssid: {ssid} channel: {channel}")
        self.hotspot.set_hostap_ssid(ssid)
        self.hotspot.set_hostap_channel(channel)
        self.hotspot.set_hostap_conf()
        self.hotspot.restart()

    def stop_hostap(self):
        """Stop host access point."""
        self.hotspot.stop()
        self.dns_server.stop()

    def restart_opennds(self):
        """Restart opennds so authenticated devices are forgotten."""
        print("restarting opennds")
        self.execute_command("systemctl restart opennds.service")

    def set_probe_req_mode(self):
        """Set network interface in probe req mode."""
        self.network_interface.set_probe_req_mode()

    def start_collecting_data(
        self, output, probe_req_only=True, time_interval_channel=10
    ):
        """Start collecting data."""
        tshark_cmd = f"{self.tshark_bin} -i {self.ext_iface} -w {output}"
        if probe_req_only:
            self.loop = asyncio.get_event_loop()
            self.loop.run_in_executor(
                None,
                self.network_interface.circular_channel_switching,
                time_interval_channel,
            )
            tshark_cmd += " -f 'wlan subtype probereq'"
        self.data_collector_process = (
            subprocess.Popen(  # pylint: disable=subprocess-popen-preexec-fn
                tshark_cmd, shell=True, preexec_fn=os.setpgrp, stdout=subprocess.PIPE
            )
        )

    def stop_collecting_data(self):
        """Stop collecting data."""
        if self.loop:
            self.loop.stop()
            self.loop = None

        if self.data_collector_process:
            os.killpg(os.getpgid(self.data_collector_process.pid), signal.SIGTERM)

        self.data_collector_process = None

    def start_collecting_ap_data(self, output):
        """Start collecting data."""
        print("Attempting to start dumpcap")
        dumpcap_cmd = "{} -i {} -b duration:{} -w {}".format(
            self.dumpcap_bin,
            self.ext_iface,
            self.dumpcap_file_generation_duration,
            output,
        )

        self.ap_data_collector_process = (
            subprocess.Popen(  # pylint: disable=subprocess-popen-preexec-fn
                dumpcap_cmd, shell=True, preexec_fn=os.setpgrp, stdout=subprocess.PIPE
            )
        )

    def stop_collecting_ap_data(self):
        """Stop collecting data."""
        if self.ap_data_collector_process:
            os.killpg(os.getpgid(self.ap_data_collector_process.pid), signal.SIGTERM)
        self.ap_data_collector_process = None

    def get_connected_users(self):
        """Get mac addresses of connected users in a list."""
        return self.hotspot.get_connected_users_advanced()

    def get_external_ip(self):
        """Get external IP address of pi."""
        try:
            return ifaddresses(self.int_iface)[AF_INET][0]["addr"]
        except KeyError:
            return "127.0.0.1"

    def nm_disable(self):
        """Disable network manager for external interface"""
        bus = dbus.SystemBus()
        nm_proxy = bus.get_object('org.freedesktop.NetworkManager', '/org/freedesktop/NetworkManager')
        nm = dbus.Interface(nm_proxy, dbus_interface='org.freedesktop.NetworkManager')

        for device_obj_path in nm.GetDevices():
            device_proxy = bus.get_object('org.freedesktop.NetworkManager', device_obj_path)
            device = dbus.Interface(device_proxy, dbus_interface='org.freedesktop.DBus.Properties')
            if device.Get('org.freedesktop.NetworkManager.Device', 'Interface') == self.ext_iface:
                device.Set('org.freedesktop.NetworkManager.Device', 'Managed', False)
