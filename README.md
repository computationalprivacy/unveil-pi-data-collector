# Pi Data Collector Python Module

This repository contains the code and instructions for installing the data collector on the rasperry pi.

## Hardware

We use [Raspberry Pi(s)](https://www.raspberrypi.org/) with an external antenna (we use [Alfa Network AWUS036NHA](https://www.alfa.com.tw/products_detail/7.htm) for our internal testing. But the data collector should work with any raspberry pi and external antenna until the platform is Kali Linux OS and all the libraries are properly installed.

## Installation instructions

### Step 1: Prepare Kali Linux SD Card for Pi

On raspberry pi, we will use Kali Linux as our OS. Refer to the [official instructions](https://www.kali.org/docs/arm/raspberry-pi/) on installing Kali Linux on Raspberry Pi.

Expected Time: 20 mins + Downloading time

**Setting up Kali Linux First Time**

Plugin in the micro SD card in Pi, attach monitor, keyboard, mouse and power supply. It will prompt for username and password on starting. The default username and password for first time users is `root` and `toor` respectively. Click on `Use default config` in the dialog box that shows up.

### Step 2: Setting up external antenna and openNDS with Kali Linux

**Step 2a: Setup conf files**

Run the following commands to generate 

```bash
cp change_me.opennds.conf opennds.conf
cp change_me.login.sh login.sh
cp change_me.dnsmasq.conf dnsmasq.conf
cp change_me.iptables.conf iptables.conf
cp change_me.nm_disable.py nm_disable.py
cp change_me.conf.ini conf.ini
```

**Step 2b: Modify opennds.conf**

Open opennds.conf in an editor and change "wlan1" on the following line to include the name of the external interface you are using (the interface of the alfa wireless adapter)

```
GatewayInterface wlan1
```

**Step 2c: Modify login.sh**

Open login.sh in an editor and change backend="1.2.3.4:8000/access/register" to point to the register endpoint on your backend (note this must be a publicly available ip address)

```
backend = "1.2.3.4:8000/access/register"
```

**Step 2d: Modify config file.**

Configuration file is available at `conf.ini`. These are the following parameters that need to be set:

- `int_iface`: Name of the internal interface that connects to WiFi for internet.
- `ext_iface`: Name of the external interface that will serves as the access point.
- `auth_code`: This is the authorization token that is set for the Pi at the backend. It ensures that only registered Pi with correct tokens can access the backend.
- `server_url`: This is the URL of the backend server.
- `wifi_ap_password`: This is the password of the access point that will be created. Ensure it is same across all the Pis.

**Note 1: dnsmasq.conf**

This file controls what IP address should be assigned for the connected devices. More details on parameters can be found [here](https://github.com/imp/dnsmasq/blob/master/dnsmasq.conf.example).

### Step 3: Install dependencies

Once the above steps are completed and you are connected to wifi, open terminal and run:

```
bash setup.sh
```

Upgrading might take a few minutes. If asked while upgrading, install the latest version available.

Dependencies include:

- [https://github.com/al45tair/netifaces](netifaces)
- [https://github.com/emlid/systemd-manager](sysdmanager)

**Notes:**

- If prompted while installing tshark, you can allow non-superusers to capture packets.

### Step 4: Setup autostart

We want to make raspberry pi a plug-and-play data collector device such that on plugging it in the power supply it should start the pi-data-collector service and connect with the backend server. To do this we have two steps.

**Step 4a: Auto login into the Pi**

To ensure the pi can login to the default user and start capturing packets as soon as it is plugged in, we modify the `lightdm` config file which is the default UI for the Kali Linux. The instructions for this can be found [here](https://wiki.archlinux.org/title/LightDM#Enabling_autologin).

**Step 4b: Auto start the pi-data-collector.**

We use supervisord to automate the restart and running the data collector. Check [supervisord README](supervisord/README.md).

## Further notes

### Reverse SSH setup

If you want to debug remotely or check if the pis are working well, then we recommend We provide details in [Reverse SSH README](reverse-ssh-setup/README.md).

## WiFi Control APIs

We provide APIs to manage data collection on WiFi using python module.

## Further reading

We use [hostapd](https://w1.fi/hostapd/) to create rogue access points and [dnsmasq](http://www.thekelleys.org.uk/dnsmasq/doc.html) for maintaining a dhcp server. We use [tshark](https://www.wireshark.org/docs/man-pages/tshark.html) to capture data. We use [opennds](https://github.com/openNDS/openNDS) to run and manage the captive portal.

## Common errors

### Hostapd is masked

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

### Hostapd start errors

If starting hostapd gives debug error, set this in config file for network manager.

```txt
[keyfile]
unmanaged-devices=mac:[mac address of external interface to exclude]
```

Alternative: Run the change_me.nm_disable.py script with the correct interface name.
