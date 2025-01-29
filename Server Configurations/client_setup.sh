#! /bin/bash

sudo apt update && sudo apt install -y wireguard
sudo mv $1 /etc/wireguard/wg0.conf
sudo wg-quick up wg0

