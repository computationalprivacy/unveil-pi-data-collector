"""Controls hostapd module.

Required controls
- start hostapd - done
- stop hostapd - done
- put interface in master mode
- create hostapd conf - done
- create persistent hostapd
- logging with hostapd
- get connected devices
"""
import os
from .wificommon import WiFi


class HostAP(WiFi):  # pylint: disable=too-many-instance-attributes
    """Hostapd controller."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        ext_iface,
        ssid="rpi",
        channel=6,
        hostapd_config="/etc/hostapd/hostapd.conf",
        hostname_config="/etc/hostname",
        wifi_ap_password="123456789",
    ):
        """Initialize HostAP."""

        super(HostAP, self).__init__(ext_iface)
        self.hostapd_path = hostapd_config
        self.hostname_path = hostname_config
        self.mac_deny_path = os.path.join(
            os.path.dirname(hostapd_config), "hostapd.deny"
        )
        self.ssid = ssid
        self.channel = channel
        self.ext_iface = ext_iface
        self.wifi_ap_password = wifi_ap_password

        if b"bin/hostapd" not in self.execute_command("whereis hostapd"):
            raise OSError("No HOSTAPD service")

        self.started = lambda: self.sysdmanager.is_active("hostapd.service")
        self.set_hostap_conf()

    def set_hostap_conf(self):
        """Set hostapd conf."""
        self.write(self.get_hostapd_conf(), self.hostapd_path)
        if not os.path.exists(self.mac_deny_path):
            self.deny_mac([])

    def get_hostapd_conf(self):
        """Return hostapd config based on interface, ssid and channel."""
        hostapd_conf_rules = [
            f"interface={self.ext_iface}",
            "driver=nl80211",
            f"ssid={self.ssid}",
            "hw_mode=g",
            f"channel={self.channel}",
            "macaddr_acl=0",
            "ignore_broadcast_ssid=0",
            "logger_syslog=1",
            "logger_syslog_level=2",
            "ap_max_inactivity=3600",
            f"deny_mac_file={self.mac_deny_path}",
            "auth_algs=1",
            "wpa=2",
            f"wpa_passphrase={self.wifi_ap_password}",
            "wpa_key_mgmt=WPA-PSK",
            "wpa_pairwise=TKIP CCMP",
            "rsn_pairwise=TKIP CCMP",
        ]
        return "\n".join(hostapd_conf_rules)

    @staticmethod
    def hostapd_control(action):
        """Control hostapd service."""
        return f"systemctl {action} hostapd.service && sleep 2"

    def start(self):
        """Start hostapd service."""
        self.execute_command(self.hostapd_control("start"))

    def stop(self):
        """Stop hostapd service."""
        self.execute_command(self.hostapd_control("stop"))

    def restart(self):
        """Restart hostapd service."""
        self.execute_command(self.hostapd_control("restart"))

    def get_hostap_ssid(self):
        """Get name of the hostapd."""
        return self.re_search("(?<=^ssid=).*", self.hostapd_path)

    def set_hostap_ssid(self, ssid="reach"):
        """Set hostapd name."""
        self.ssid = ssid

    def set_hostap_channel(self, channel=1):
        """Set hostap channel."""
        self.channel = channel

    def set_hostap_password(self, password):
        """Set hostapd password."""
        self.replace(
            "^wpa_passphrase=.*", f"wpa_passphrase={password}", self.hostapd_path
        )
        return self.verify_hostap_password(password)

    def verify_hostap_password(self, value):
        """Verify hostapd password."""
        return self.re_search("(?<=^wpa_passphrase=).*", self.hostapd_path) == value

    def set_host_name(self, name="reach"):
        """Set name of the host."""
        try:
            with open(self.hostname_path, "w", 0) as hostname_file:
                hostname_file.write(name + "\n")
                hostname_file.flush()
                os.fsync(hostname_file)
        except IOError:
            pass
        else:
            self.execute_command(f"hostname -F {self.hostapd_path}")

    def get_host_name(self):
        """Get name of the host."""
        return self.re_search("^.*", self.hostname_path)

    @staticmethod
    def _check_valid_mac(mac):
        """Check if it is a valid mac address."""
        return len(mac.split(":")) == 6

    def get_connected_users(self):
        """Get mac addresses of connected users in a list."""
        output = self.execute_command(f"arp -a -n -i {self.ext_iface}")
        output = output.decode("utf8").strip().split("\n")
        connected_mac = []
        for line in output:
            components = line.split(" ")
            if self._check_valid_mac(components[3]):
                connected_mac.append(components[3])
        return connected_mac

    def get_connected_users_advanced(self):
        """Get mac addresses of connected users in a list."""
        inactive_threshold = 10000  # in ms
        output = (
            self.execute_command(f"iw dev {self.ext_iface} station dump")
            .decode("utf8")
            .strip()
            .lower()
            .split("\n")
        )
        connected_mac = []
        mac = None
        for line in output:
            if line.find("station") != -1:
                mac = line.strip().split()[1]
                if not self._check_valid_mac(mac):
                    mac = None
            if line.find("inactive time") != -1 and mac:
                inactive_time = int(line.strip().split(":")[1].strip().split()[0])
                if inactive_time < inactive_threshold:
                    connected_mac.append(mac)
                mac = None
        return connected_mac

    def deny_mac(self, mac_list):
        """Write mac list to a file."""
        self.write("\n".join(mac_list), self.mac_deny_path)


if __name__ == "__main__":
    hotspot = HostAP("wlp6s0")
