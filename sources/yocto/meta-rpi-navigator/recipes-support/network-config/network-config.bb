SUMMARY = "Network configuration for rpi"
LICENSE = "Apache-2.0"
LIC_FILES_CHKSUM = "file://hostapd.conf;md5=1dad626efccbef8c8e50e2dc5a1c293a"

SRC_URI = " \
    file://hostapd.conf \
    file://dnsmasq.conf \
    file://network-init.sh \
"

S = "${WORKDIR}"

do_install() {
    install -d ${D}${sysconfdir}/hostapd
    install -m 0644 ${WORKDIR}/hostapd.conf \
        ${D}${sysconfdir}/hostapd/hostapd-rpi.conf

    install -d ${D}${sysconfdir}/dnsmasq.d
    install -m 0644 ${WORKDIR}/dnsmasq.conf \
        ${D}${sysconfdir}/dnsmasq.d/rpi.conf

    install -d ${D}${sysconfdir}/init.d
    install -m 0755 ${WORKDIR}/network-init.sh \
        ${D}${sysconfdir}/init.d/network-init

    install -d ${D}${sysconfdir}/rcS.d
    ln -sf ../init.d/network-init \
        ${D}${sysconfdir}/rcS.d/S99network-init
}

FILES:${PN} += " \
    ${sysconfdir}/hostapd/hostapd-rpi.conf \
    ${sysconfdir}/dnsmasq.d/rpi.conf \
    ${sysconfdir}/init.d/network-init \
    ${sysconfdir}/rcS.d/S99network-init \
"
