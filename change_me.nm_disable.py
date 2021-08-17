"""Script to un-manage a network interface"""
import dbus


UNMANAGED_DEVICE = (
    "wlan1"  # update this variable to dictate the device we're un-managing
)
bus = dbus.SystemBus()

nm_proxy = bus.get_object(
    "org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager"
)
nm = dbus.Interface(nm_proxy, dbus_interface="org.freedesktop.NetworkManager")

for device_obj_path in nm.GetDevices():
    device_proxy = bus.get_object("org.freedesktop.NetworkManager", device_obj_path)
    device = dbus.Interface(
        device_proxy, dbus_interface="org.freedesktop.DBus.Properties"
    )
    if (
        device.Get("org.freedesktop.NetworkManager.Device", "Interface")
        == UNMANAGED_DEVICE
    ):
        device.Set("org.freedesktop.NetworkManager.Device", "Managed", False)
