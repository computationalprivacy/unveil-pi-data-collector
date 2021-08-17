"""
Tests for dnsmasq
"""
import sys
from unittest.mock import MagicMock, patch, call, ANY

mock_sysdmanager = MagicMock()
sys.modules["sysdmanager"] = mock_sysdmanager
from src.dnsmasq import DNSMasq


def mock_init(self, ext_iface, int_iface):
    self.iptables_config = "None"
    self.ext_iface = ext_iface
    self.int_iface = int_iface


@patch.object(DNSMasq, "__init__", mock_init)
@patch("src.dnsmasq.DNSMasq.execute_command", autospec=True)
def test_initialization(mock_execute):
    mock_dnsmasq = DNSMasq("wlan0", "wlan1")
    mock_dnsmasq.initialize_dnsmasq()
    print(mock_execute.mock_calls)
    mock_execute.assert_has_calls([
        call(ANY, "ip route delete 192.168.1.0/24"),
        call(ANY, "ifconfig wlan0 up 192.168.1.1 netmask 255.255.255.0"),
        call(ANY, 'route add -net 192.168.1.0 netmask 255.255.255.0 gw 192.168.1.1'),
        call(ANY, 'echo 1 > /proc/sys/net/ipv4/ip_forward'),
        call(ANY, 'iptables -A FORWARD -i wlan1 -o wlan0 -m state --state ESTABLISHED,RELATED -j ACCEPT'),
        call(ANY, 'iptables -A FORWARD -i wlan0 -o wlan1 -j ACCEPT'),
        call(ANY, 'iptables -t nat -A POSTROUTING -o wlan1 -j MASQUERADE'),
    ])
