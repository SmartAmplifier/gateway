# gateway

Gateway is bridge between Smart-Amplifier Cloud and hardware. It run's for example on Raspberry Pi as service. It needs some additional software to run. It has also user interface for adding new amplifiers and showing IDs of already paired ones:

![User interface"](doc/img/user_interface.png)

It is located via Web Browser on device IP adress of DNS name [http://smart-amplifier-gateway.local/](http://smart-amplifier-gateway.local/).

## Install on vanilla Raspbian

First we need to install BigClown tools. They are bridge between usb serial communication and MQTT protocol. First install pip3

    sudo apt-get install python3-pip

For MQTT protocol we need MQTT broker. We will install mosquito

    sudo apt install mosquitto mosquitto-clients

Then we need bcg which stands for BigClown Gateway

    sudo pip3 install bcg

Add udev rules for BigClown Radio Dongle

    echo 'SUBSYSTEMS=="usb", ACTION=="add", KERNEL=="ttyUSB*", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6015", ATTRS{serial}=="bc-usb-dongle*", SYMLINK+="bcUD%n", TAG+="systemd", ENV{SYSTEMD_ALIAS}="/dev/bcUD%n"'  | sudo tee --append /etc/udev/rules.d/58-bigclown-usb-dongle.rules

Now run bcg service via systemd process manager

    sudo nano /etc/systemd/system/bcg.service

Paste following

```
[Unit]
Description=BigClown Gateway
After=network.target

[Service]
Type=simple
User=pi
ExecStart=/usr/local/bin/bcg -d /dev/bcUD0
Restart=always
RestartSec=5
StartLimitIntervalSec=0

[Install]
WantedBy=multi-user.target
```
Start bcg service

    sudo systemctl start bcg

Enable bcg service on boot

    sudo systemctl enable bcg

Now install requirements Python packages for gateway.

    sudo pip3 install -r requirements.txt

Run gateway service also via systemd config

    sudo nano /etc/systemd/system/gateway.service

And instert following. Replace `<DIR>` with path where script is located. You can print actual path:

    echo $PWD

```
[Unit]
Description=Smart Amplifier Gateway
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=<DIR>
ExecStart=/usr/bin/python3 gateway.py
Restart=always
RestartSec=5
StartLimitIntervalSec=0

[Install]
WantedBy=multi-user.target
```

Start gateway service

    sudo systemctl start gateway

Enable gateway service on boot

    sudo systemctl enable gateway

Forward port from 80 to 8080

    iptables -t nat -A PREROUTING -p tcp --dport 80 -j DNAT --to-destination 127.0.0.1:8080

Install `iptables-persistent`

    sudo apt-get install iptables-persistent

Save `iptables` config

    sudo service iptables save