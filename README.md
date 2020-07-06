# Pi Data Collector Python Module

## Setup Pi

### Prepare Kali Linux SD Card for Pi

On raspberry pi, we will use Kali Linux as our OS. From [Offensive Security](https://www.offensive-security.com/kali-linux-arm-images/), download the latest version of Kali Linux for Raspberry Pi 2 and 3. Use [Etcher](https://etcher.io/) to burn the image to the SD Card. Start the Etcher ([On Linux](https://www.omgubuntu.co.uk/2017/05/how-to-install-etcher-on-ubuntu)) and flashing OS is simply 3 clicks. 

Expected Time: 20 mins + Downloading time

### Setting up Kali Linux First Time

Plugin in the micro SD card in Pi, attach monitor, keyboard, mouse and power supply. It will prompt for username and password on starting. The default username and password for first time users is `root` and `toor` respectively. Click on `Use default config` in the dialog box that shows up.

### Setting up Alfa Wireless AWUS036NHA with Kali Linux

Once the Kali Linux is setup and connected to wifi, open terminal and run:

```
bash setup.sh
```

Upgrading might take a few minutes. If asked while upgrading, install the latest version available. 

### Notes:

- If prompted while installing tshark, you can allow non-superusers to capture packets.

## Reverse SSH setup

We provide details in [Reverse SSH README](reverse-ssh-setup/README.md).

## WiFi Control APIs

We provide APIs to manage data collection on WiFi using python module.

### Read

We use [hostapd](https://w1.fi/hostapd/) to create rogue access points and [dnsmasq](http://www.thekelleys.org.uk/dnsmasq/doc.html) for maintaining a dhcp server. We use [tshark](https://www.wireshark.org/docs/man-pages/tshark.html) to capture data.

### Requirements

- [https://github.com/al45tair/netifaces](netifaces)
- [https://github.com/emlid/systemd-manager](sysdmanager)

### Notes

If hostapd service is masked use this:

```bash

# if below command does not work

systemctl start hostapd

# if it gives unit hostapd.service masked
# run following commands

systemctl unmask hostapd
systemctl enable hostapd
systemctl restart hostapd
```

#### Hostapd Start Errors

If starting hostapd gives debug error, set this in config file for network manager.

```txt
[keyfile]
unmanaged-devices=mac:[mac address of external interface to exclude]
```

## Setup configuration file

```shell
cp change_me.conf.ini conf.ini
```

Configuration file is available at `conf.ini`. These are the following parameters that need to be set:

- `int_iface`: Name of the internal interface that connects to WiFi for internet.
- `ext_iface`: Name of the external interface that will serves as the access point.
- `auth_code`: This is the authorization token that is set for the Pi at the backend. It ensures that only registered Pi with correct tokens can access the backend.
- `server_url`: This is the URL of the backend server.
- `wifi_ap_password`: This is the password of the access point that will be created. Ensure it is same across all the Pis.

## Setup autostart

Check supervisord README.
