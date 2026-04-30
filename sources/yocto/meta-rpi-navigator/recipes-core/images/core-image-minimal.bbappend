########################################
#  Headless
########################################
IMAGE_FEATURES:remove = "x11-base"
DISTRO_FEATURES:remove = "x11 wayland gtk"

########################################
# Networking
########################################
IMAGE_INSTALL:append = " \
    hostapd \
    dnsmasq \
    iproute2 \
    ethtool \
    iptables \
    iw  \
    network-config \
    kernel-module-brcmfmac \
    kernel-module-brcmutil \
    linux-firmware-rpidistro-bcm43455 \
    linux-firmware-rpidistro-broadcom-license \
"

########################################
# Python 
########################################
IMAGE_INSTALL:append = " \
    python3 \
    python3-numpy \
    python3-opencv \
    python3-ctypes \
    python3-json \
"

########################################
# TensorFlow Lite
########################################
IMAGE_INSTALL:append = " \
    tensorflow-lite \
"

########################################
# GStreamer (decode / encode / MJPEG)
########################################
IMAGE_INSTALL:append = " \
    gstreamer1.0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-libav \
    gstreamer1.0-plugins-good-isomp4 \
"

########################################
# Debug
########################################
IMAGE_INSTALL:append = " \
    htop \
    procps \
    nano \
"

#Network
IMAGE_INSTALL:append = " \
    ca-certificates \
    git \
    curl \
    wget \
"
########################################
# Server ssh
########################################
IMAGE_FEATURES:append = " ssh-server-dropbear"

########################################
# Main APP
########################################
IMAGE_INSTALL:append = " navigator"

