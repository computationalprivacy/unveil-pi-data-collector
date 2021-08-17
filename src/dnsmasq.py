"""Control DNSMasq service.

- stop dhcp
- setup dhcp conf
    + setup dhcp config file
    + ip route delete 192.168.1.0/24
    + ifconfig wlan1 up 192.168.1.1 netmask 255.255.255.0
    + route add -net 192.168.1.0 netmask 255.255.255.0 gw 192.168.1.1
- start dhcp
- setup internet forwarding
    + iptables --table nat --append POSTROUTING --out-interface wlan0
      -j MASQUERADE
    + iptables --append FORWARD --in-interface wlan1 -j ACCEPT
"""
import subprocess

from .wificommon import WiFi, WiFiControlError


class DNSMasq(WiFi):
    """DNSMasq controller."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        ext_iface,
        int_iface,
        dnsmasq_config="/etc/dnsmasq.d/dnsmasq.conf",
        dnsmasq_config_defaults="dnsmasq.conf",
        iptables_config="iptables.conf",
    ):

        """Initalize dnsmasq controller."""
        super(DNSMasq, self).__init__(ext_iface)
        self.iptables_config = iptables_config
        self.dnsmasq_config_defaults = dnsmasq_config_defaults
        self.ext_iface = ext_iface
        self.int_iface = int_iface
        self.dnsmasq_config = dnsmasq_config

        if b"bin/dnsmasq" not in self.execute_command("whereis dnsmasq"):
            raise OSError("No DNSMASQ service")

        self.started = lambda: self.sysdmanager.is_active("dnsmasq.service")
        self.set_dnsmasq_conf()
        self.initialize_dnsmasq()

    def set_dnsmasq_conf(self):
        """Set dnsmasq conf."""
        try:
            with open(self.dnsmasq_config_defaults, "r") as defaults:
                self.write(defaults.read(), self.dnsmasq_config)
        except FileNotFoundError:
            self.write(self.get_dnsmasq_conf(), self.dnsmasq_config)

    def get_dnsmasq_conf(self):
        """Set the dnsmasq conf."""
        dnsmasq_conf_rules = [
            f"interface={self.ext_iface}",
            "dhcp-range=192.168.1.2,192.168.1.30,12h",
            "dhcp-option=1,255.255.255.0",
            "dhcp-option=3,192.168.1.1",
            "dhcp-option=6,192.168.1.1",
            "server=8.8.8.8",
            "log-queries",
            "log-dhcp",
            "listen-address=127.0.0.1",
        ]
        return "\n".join(dnsmasq_conf_rules)

    @staticmethod
    def dnsmasq_control(action):
        """Control dnsmasq service."""
        return f"systemctl {action} dnsmasq.service && sleep 2"

    def initialize_dnsmasq(self):
        """Initialize dnsmasq setup on machine for easy routing."""
        try:
            args = {}
            with open(self.iptables_config, "r") as defaults:
                for line in defaults:
                    (key, val) = line.strip().split("=")
                    args[key] = val
                subnet = args["subnet"]
                gateway = args["gateway"]
        except FileNotFoundError:
            subnet = "192.168.1.0"
            gateway = "192.168.1.1"

        try:
            self.execute_command(f"ip route delete {subnet}/24")
        except (subprocess.CalledProcessError, WiFiControlError) as error:
            print(f"Error: {error}")

        self.execute_command(
            f"ifconfig {self.ext_iface} up {gateway} netmask 255.255.255." "0"
        )
        self.execute_command(
            f"route add -net {subnet} netmask 255.255.255.0" f" gw {gateway}"
        )

        # Code below sets up Packet Forwarding from wlan1 (antenna) to wlan0
        # (raspi's wifi nic)
        self.execute_command("echo 1 > /proc/sys/net/ipv4/ip_forward")
        self.execute_command(
            f"iptables -A FORWARD -i {self.int_iface} -o {self.ext_iface} -m state "
            f"--state ESTABLISHED,RELATED -j ACCEPT"
        )
        self.execute_command(
            f"iptables -A FORWARD -i {self.ext_iface} -o {self.int_iface} -j ACCEPT"
        )
        self.execute_command(
            f"iptables -t nat -A POSTROUTING -o {self.int_iface} -j MASQUERADE"
        )

    def start(self):
        """Start dnsmasq service."""
        self.execute_command(self.dnsmasq_control("start"))

    def stop(self):
        """Stop dnsmasq service."""
        self.execute_command(self.dnsmasq_control("stop"))

    def restart(self):
        """Restart hostapd service."""
        self.execute_command(self.dnsmasq_control("restart"))
