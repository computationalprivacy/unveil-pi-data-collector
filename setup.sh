#!/bin/bash

# setup system

apt-get update
apt-get upgrade -y

apt-get update
apt-get install -y firmware-atheros curl

# install python
apt-get install python3-dev python3-pip python3-setuptools

# install dependencies for tshark
apt-get install tshark

# install required packages for wifi control
apt-get install -y hostapd dnsmasq

# installing netifaces
pip3 install netifaces requests configargparse dbus-python

# installing systemd-manager
sudo apt install dbus libdbus-glib-1-dev libdbus-1-dev
pip3 install git+https://github.com/emlid/systemd-manager.git#egg=sysdmanager

# uninstall libmicrohttpd12 to install opennds https://opennds.readthedocs.io/en/stable/compile.html
sudo apt remove libmicrohttpd12

# create temporary install directory
mkdir tmp
cd tmp

# install old version of libmicrohttpd
wget https://ftp.gnu.org/gnu/libmicrohttpd/libmicrohttpd-0.9.70.tar.gz
tar  -xf libmicrohttpd-0.9.70.tar.gz
cd libmicrohttpd-0.9.70
./configure --disable-https
make
sudo make install
sudo ldconfig
cd ..

# install opennds
wget https://codeload.github.com/opennds/opennds/tar.gz/v5.2.0
tar -xf v5.2.0
cd openNDS-5.2.0
make
sudo make install
sudo systemctl enable opennds

cd ../..
rm -rf tmp

cp ./opennds.conf /etc/opennds/opennds.conf
cp ./login.sh /usr/lib/opennds/login.sh
cp ./logo.png /etc/opennds/htdocs/images/logo.png
chmod u+x /usr/lib/opennds/login.sh

# install watchdog - Had to make sudo to add to path. (might not need if whole command is run as sudo)
sudo pip3 install watchdog
