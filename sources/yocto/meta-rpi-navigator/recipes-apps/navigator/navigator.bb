SUMMARY = "Navigator – Video inference headless (TFLite + GStreamer)"
LICENSE = "CLOSED"

SRC_URI = "git://github.com/Taller-Embebidos/Proyecto_2.git;branch=main;protocol=https"
SRCREV = "${AUTOREV}"
S = "${WORKDIR}/git"

DEPENDS = "\
    python3-native \
    opencv \
    gstreamer1.0 \
"

RDEPENDS:${PN} = "\
    python3 \
    python3-opencv \
    python3-numpy \
    tensorflow-lite \
    gstreamer1.0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-libav \
"

do_install() {
    install -d ${D}${datadir}/navigator

    install -m 0755 ${S}/src/semaforo.py ${D}${datadir}/navigator/
    install -m 0644 ${S}/src/yolo11n_float16.tflite ${D}${datadir}/navigator/
    install -m 0644 ${S}/src/labels.txt ${D}${datadir}/navigator/
    install -m 0644 ${S}/src/video_test.mp4 ${D}${datadir}/navigator/
}

FILES:${PN} += "\
    ${datadir}/navigator \
"

INSANE_SKIP:${PN} += "already-stripped"
