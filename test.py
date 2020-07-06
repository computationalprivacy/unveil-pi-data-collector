"""Test for wifi."""
from src.wifi import WiFiHandler
import time
import requests


wifi = WiFiHandler('wlan1', 'wlan0')
# wifi.init_wifi()
wifi.set_probe_req_mode()
mac = wifi.get_device_mac()
print(mac)
# while(True):
#     # response = requests.get('http://www.google.com')
#     response = requests.post(
#         'http://146.169.32.219:8000/status/update/', data={
#             'mac': mac,
#             'status': 'PROBE_REQ'}, timeout=20)
#     print(response.json())
#     time.sleep(5)

# wifi.set_hostap_mode()
# wifi.change_hostap('EurostarTrainsWiFi', 6)
# while True:
#     print(wifi.get_connected_users())
#     time.sleep(300)
print("Data collection starting.")
wifi.start_collecting_data(
    'collection_data.pcapng', probe_req_only=True)
time.sleep(60)
print("Data collection stopping.")
wifi.stop_collecting_data()

# while True:
#     pass
