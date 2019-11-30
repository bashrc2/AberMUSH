#!/bin/bash
INSTALL_PACKAGE="sudo apt-get -y install"
PYTHON_PACKAGE="python3"
if [ -f /usr/bin/pacman ]; then
    INSTALL_PACKAGE="sudo pacman -S --noconfirm"
    PYTHON_PACKAGE="python"
fi
$INSTALL_PACKAGE $PYTHON_PACKAGE
$INSTALL_PACKAGE $PYTHON_PACKAGE-pip
yes | sudo pip3 install commentjson
yes | sudo pip3 install websocket-client
$INSTALL_PACKAGE git-core
if [ ! -d /opt/abermush ]; then
    sudo git clone https://code.freedombone.net/bashrc/AberMUSH /opt/abermush
fi
if [ -d /etc/systemd/system ]; then
    sudo cp /opt/abermush/abermush.service /etc/systemd/system/abermush.service
    sudo systemctl enable abermush
    sudo systemctl restart abermush
fi
