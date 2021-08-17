"""Network interface manager."""
import asyncio
import itertools
from .wificommon import WiFi


class NetworkInterface(WiFi):
    """Network interface manager."""

    def __init__(
        self, interface, network_manager_conf="/etc/NetworkManager/NetworkManager.conf"
    ):
        """Initialize network interface to set up for hotspot."""
        super(NetworkInterface, self).__init__(interface)
        self.interface = interface
        self.current_mode = None
        self.network_manager_conf = network_manager_conf

    def init_network(self):
        """Initialize network manager setup."""
        self.switch_network(0)
        self.write(self.get_network_conf(), self.network_manager_conf)
        self.execute_command("service network-manager restart")
        self.switch_network(1)

    def set_probe_req_mode(self):
        """Change mode of interface to probe request mode."""
        self.change_interface_mode("monitor")

    def set_hostap_mode(self):
        """Set hostapd mode."""
        self.change_interface_mode("monitor")

    def switch_network(self, action):
        """Switch interface w.r.t mentioned action."""
        action = "down" if action == 0 else "up"
        self.execute_command(f"ifconfig {self.interface} {action}")

    def change_interface_mode(self, mode):
        """Change mode at which interface operates."""
        self.switch_network(0)
        self.execute_command(f"iwconfig {self.interface} mode {mode}")
        self.switch_network(1)
        self.current_mode = mode

    def get_network_conf(self):
        """Return network conf."""
        network_conf = [
            "[main]",
            "plugins=ifupdown,keyfile",
            "",
            "[ifupdown]",
            "managed=false",
            "",
            "[keyfile]",
            f"unmanaged-devices=interface-name:{self.interface}",
        ]
        return "\n".join(network_conf)

    def set_channel(self, channel):
        """Set channel of interface."""
        self.execute_command(f"iwconfig {self.interface} channel {channel}")

    def circular_channel_switching(self, time_interval):
        """Async function to cycle through channels."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        for i in itertools.cycle(range(1, 12)):
            self.set_channel(i)
            loop.run_until_complete(asyncio.sleep(time_interval))
