#!/bin/bash

sudo wg-quick down wg0
sudo systemctl stop wg-quick@wg0
sudo systemctl disable wg-quick@wg0
sudo ip link delete wg0
sudo apt-get purge wireguard wireguard-tools
sudo rm -rf /etc/wireguard
sudo apt-get autoremove
sudo rm -rf users.db ip_allocation.db
sudo killall wg
