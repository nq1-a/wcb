#!/bin/bash

distro=`grep --color=never -Po '(?<=ID_LIKE="?)[a-z0-9]*(?="?)' /etc/os-release`

if [[ distro == "" ]]; then
    distro=`grep --color=never -Po '(?<=ID="?)[a-z0-9]*(?="?)' /etc/os-release`
fi

case $distro in
    arch)
        sudo pacman -Sy espeak-ng
        ;;
    debian)
        sudo apt install espeak-ng
        ;;
    *) echo "" ;;
esac
