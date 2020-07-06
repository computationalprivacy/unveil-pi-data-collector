# Reverse SSH Setup

## What does reverse ssh mean?

Let us assume, you have a device (say `Pi`) which connects to random ip addresses everytime it starts and you want to login into device without knowing the IP. [Reverse SSH Tunneling](https://unix.stackexchange.com/questions/46235/how-does-reverse-ssh-tunneling-work) is one possible solution. In simple words, you create a tunnel from `Pi` via SSH into another device (say `host`) but in a reverse direction, so that you can login into `Pi` from the `host` via SSH. 

e.g. 

Running `ssh -R 20000:localhost:22 username@host` on `Pi` will create a tunnel from `Pi` to `host`. You can login to `Pi` from `host` using `ssh pi@localhost -p 20000` where `pi` is the user on `Pi` and 20000 is the port on `host` we have chosen to create tunnel in.

## Requirements

- A machine where you can ssh without requiring the password, let that machine be `username@host`
- Install [autossh](https://www.systutorials.com/docs/linux/man/1-autossh/)  - `sudo apt-get install autossh`. It ensures a persistent connection via ssh.
- Check that following command works
```bash
su -c "autossh -M 0 -f -N -R 20000:localhost:22 username@host -o LogLevel=error -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no" root
```

## Setup

We want to start the reverse ssh tunnel as soon as the pi starts. So we will start the autossh as soon as network is up. 

```bash
cp autossh /etc/network/if-up.d/
```

Another issue, we face when starting is that network wlan interfaces connect to the APs once they are logged in. Which means, we have to manually login to the interface each time and then it will connect to the WLAN AP and then the reverse ssh will be connected. This is pretty convoluted approach and to enable Pi to connect to WLAN AP without login, follow the below steps:

```bash
# gdm3 setup
cp daemon.conf /etc/gdm3/

# lightdm setup
cp lightdm.conf /etc/lightdm/
```

## References

- [https://dephace.com/raspberry-pi-3-kali-linux-auto-login/](https://dephace.com/raspberry-pi-3-kali-linux-auto-login/)
- [https://www.ifnull.org/articles/setting_up_raspberry_pi/](https://www.ifnull.org/articles/setting_up_raspberry_pi/)
- [https://www.binarytides.com/auto-login-root-user-kali/](https://www.binarytides.com/auto-login-root-user-kali/)
- [https://emtunc.org/blog/07/2016/reverse-ssh-tunnelling-ssl-raspberry-pi/](https://emtunc.org/blog/07/2016/reverse-ssh-tunnelling-ssl-raspberry-pi/)
- [https://blog.sleeplessbeastie.eu/2014/12/23/how-to-create-persistent-reverse-ssh-tunnel/](https://blog.sleeplessbeastie.eu/2014/12/23/how-to-create-persistent-reverse-ssh-tunnel/)