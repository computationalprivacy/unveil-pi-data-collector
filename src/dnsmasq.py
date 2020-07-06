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
from .wificommon import WiFi


class DNSMasq(WiFi):
    """DNSMasq controller."""

    def __init__(
        self, interface, internet_interface,
            dnsmasq_config='/etc/dnsmasq.d/dnsmasq.conf'):
        """Initalize dnsmasq controller."""
        super(DNSMasq, self).__init__(interface)
        self.interface = interface
        self.internet_interface = internet_interface
        self.dnsmasq_config = dnsmasq_config

        if (b'bin/dnsmasq' not in self.execute_command("whereis dnsmasq")):
            raise OSError('No DNSMASQ service')

        self.started = lambda: self.sysdmanager.is_active("dnsmasq.service")
        self.set_dnsmasq_conf()
        self.initialize_dnsmasq()

    def set_dnsmasq_conf(self):
        """Set dnsmasq conf."""
        self.write(self.get_dnsmasq_conf(), self.dnsmasq_config)

    def get_dnsmasq_conf(self):
        """Set the dnsmasq conf."""
        dnsmasq_conf_rules = [
            'interface={}'.format(self.interface),
            'dhcp-range=192.168.1.2,192.168.1.30,12h',
            'dhcp-option=1,255.255.255.0',
            'dhcp-option=3,192.168.1.1',
            'dhcp-option=6,192.168.1.1',
            'server=8.8.8.8',
            'log-queries',
            'log-dhcp',
            'listen-address=127.0.0.1'
        ]
        return '\n'.join(dnsmasq_conf_rules)

    def dnsmasq_control(self, action):
        """Control dnsmasq service."""
        return "systemctl {} dnsmasq.service && sleep 2".format(action)

    def initialize_dnsmasq(self):
        """Initialize dnsmasq setup on machine for easy routing."""
        while(True):
            try:
                self.execute_command("ip route delete 192.168.1.0/24")
            except Exception:
                break
        self.execute_command("ifconfig {} up 192.168.1.1 netmask 255.255.255."
                             "0".format(self.interface))
        self.execute_command("route add -net 192.168.1.0 netmask 255.255.255.0"
                             " gw 192.168.1.1")
        self.execute_command("iptables --table nat --append POSTROUTING "
                             "--out-interface {} -j MASQUERADE".
                             format(self.internet_interface))
        self.execute_command("iptables --append FORWARD --in-interface {} "
                             "-j ACCEPT".format(self.interface))
        self.execute_command("echo 1 > /proc/sys/net/ipv4/ip_forward")

    def start(self):
        """Start dnsmasq service."""
        self.execute_command(self.dnsmasq_control("start"))

    def stop(self):
        """Stop dnsmasq service."""
        self.execute_command(self.dnsmasq_control("stop"))

    def restart(self):
        """Restart hostapd service."""
        self.execute_command(self.dnsmasq_control("restart"))
