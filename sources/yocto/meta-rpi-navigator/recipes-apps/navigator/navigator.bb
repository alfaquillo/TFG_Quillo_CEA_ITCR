SUMMARY = "Intelligent navigation ELANAV"
LICENSE = "Apache-2.0"
LIC_FILES_CHKSUM = "file://LICENSE;md5=86d3f3a95c324c9479bd8986968f4327"

SRC_URI = "git://github.com/alfaquillo/TFG_Quillo_CEA_ITCR.git;branch=main;protocol=https"
SRCREV = "${AUTOREV}"
S = "${WORKDIR}/git"

DEPENDS = "\
    python3-native \
    opencv \
    gstreamer1.0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
"

RDEPENDS:${PN} = "\
    python3 \
    python3-opencv \
    python3-numpy \
    tensorflow-lite \
    python3-ctypes \
    python3-json \
    bash \
    gstreamer1.0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    gstreamer1.0-plugins-good-isomp4 \
"

do_install() {
    install -d ${D}${bindir}
    install -d ${D}${datadir}/navigation

    cat > ${D}${bindir}/navigation << 'SCRIPT'
#!/bin/sh
echo "========================================"
echo "   INTELLIGENT NAVIGATION - TFLITE"
echo "========================================"

cd /usr/share/navigation
exec python3 main.py
SCRIPT

    chmod 0755 ${D}${bindir}/navigation

    # Copy all files from sources/navigation
    cp -r ${S}/sources/navigation/* ${D}${datadir}/navigation/

    # Set permissions
    find ${D}${datadir}/navigation -type f -exec chmod 0644 {} \;
    find ${D}${datadir}/navigation -type d -exec chmod 0755 {} \;
}

FILES:${PN} += "\
    ${bindir}/navigation \
    ${datadir}/navigation \
"

INSANE_SKIP:${PN} += "already-stripped"
