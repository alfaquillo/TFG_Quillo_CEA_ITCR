#!/bin/sh

LOG=/tmp/network-init.log

log() {
    echo "[NET] $1" | tee -a $LOG
}

wait_iface() {
    IFACE=$1
    TIMEOUT=30
    COUNT=0

    while [ $COUNT -lt $TIMEOUT ]; do
        if ip link show "$IFACE" >/dev/null 2>&1; then
            log "$IFACE detected"
            return 0
        fi
        sleep 1
        COUNT=$((COUNT+1))
    done

    log "timeout waiting for $IFACE"
    return 1
}

wait_wlan_ready() {
    TIMEOUT=30
    COUNT=0

    while [ $COUNT -lt $TIMEOUT ]; do
        iw dev wlan0 info >/dev/null 2>&1 && {
            log "wlan0 ready"
            return 0
        }
        sleep 1
        COUNT=$((COUNT+1))
    done

    log "timeout waiting wlan0 ready"
    return 1
}

log "network init start"

udevadm settle

# Ethernet 
if wait_iface eth0; then
    ip link set eth0 up
    udhcpc -n -q -t 3 -i eth0 || true
fi

# WiFi 
wait_iface wlan0 || exit 1
wait_wlan_ready || exit 1

ip link set wlan0 up
sleep 1

ip addr flush dev wlan0 || true
ip addr add 192.168.3.1/24 dev wlan0 || true

iw dev wlan0 set power_save off || true

pkill hostapd 2>/dev/null || true
pkill dnsmasq 2>/dev/null || true

hostapd /etc/hostapd/hostapd-rpi.conf -B || exit 1
sleep 2
dnsmasq --conf-file=/etc/dnsmasq.d/rpi.conf || exit 1

log "network init done"
