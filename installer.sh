#!/bin/bash
INSTALL_PACKAGE="sudo apt-get -y install"
PYTHON_PACKAGE="python3"
if [ -f /usr/bin/pacman ]; then
    INSTALL_PACKAGE="sudo pacman -S --noconfirm"
    PYTHON_PACKAGE="python"
fi
$INSTALL_PACKAGE telnet
$INSTALL_PACKAGE $PYTHON_PACKAGE
$INSTALL_PACKAGE $PYTHON_PACKAGE-pip
$INSTALL_PACKAGE $PYTHON_PACKAGE-dateutil
$INSTALL_PACKAGE $PYTHON_PACKAGE-websocket
$INSTALL_PACKAGE git-core
if [ ! -d /opt/abermush ]; then
    sudo useradd -d /opt/abermush/ abermush
    sudo git clone https://code.freedombone.net/bashrc/AberMUSH /opt/abermush
    chown -R abermush:abermush abermush
fi
if [ -d /etc/systemd/system ]; then
    sudo cp /opt/abermush/abermush.service /etc/systemd/system/abermush.service
    sudo systemctl enable abermush
    sudo systemctl restart abermush
fi
