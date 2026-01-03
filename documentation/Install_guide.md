
# Guía de creación y uso del contenedor Ubuntu 24.04 para Yocto (Raspberry Pi 5)

Entorno Host: Fedora 43 usando Toolbox o Podman

---

## 1. Preparación del entorno en el host

Instalar Toolbox (recomendado) o Podman:


```bash
sudo dnf -y install toolbox
sudo dnf -y install podman
```

Crear un directorio de trabajo para contenedores e imágenes:

```bash
mkdir -p ~/tools/containers/ubuntu-toolbox-yocto
cd ~/tools/containers/ubuntu-toolbox-yocto
```
---

## 2. Crear el Containerfile

Crear un archivo llamado `Containerfile` con el siguiente contenido:

```bash
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

RUN apt update && apt install -y \
    sudo passwd ca-certificates dbus-user-session locales \
    build-essential chrpath cpio debianutils diffstat file \
    gawk gcc g++ git iputils-ping libacl1 liblz4-tool \
    python3 python3-git python3-jinja2 python3-pexpect \
    python3-pip python3-setuptools socat texinfo unzip \
    wget xz-utils zstd \
    && rm -rf /var/lib/apt/lists/*

RUN locale-gen en_US.UTF-8

RUN echo "%sudo ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/toolbox \
    && chmod 0440 /etc/sudoers.d/toolbox

RUN set -eux; \
    if getent passwd 1000; then \
        userdel -r $(getent passwd 1000 | cut -d: -f1) || true; \
    fi
```
---

## 3. Construir la imagen

```bash
podman build -t ubuntu-toolbox-yocto:24.04 .
``` 
Verifica que la imagen se creó:

```bash
podman images | grep yocto
``` 
---

## 4. Crear el contenedor

### Usando Toolbox (recomendado):

```bash
toolbox create -i ubuntu-toolbox-yocto:24.04 yocto
```

### Usando Podman:

```bash
podman run -it --name yocto \
    -v /home/<user>/tools:/tools:z \
    ubuntu-toolbox-yocto:24.04 /bin/bash
```
Notas:

- Reemplaza `<user>` por tu usuario.
- Toolbox mantiene rutas del host (~/tools), Podman las monta en /tools.
- La imagen Ubuntu 24.04 se usa como contenedor con alias 'yocto'.

---

## 5. Ingreso al contenedor

### Toolbox:

```bash
toolbox enter yocto
```
### Podman:

```bash
podman start -ai yocto
```
El contenedor ya tiene configurado un usuario no root <user> con UID 1000, que es el mismo que tu usuario del host. Por eso no necesitas crear un usuario adicional.

5. Preparación del entorno Yocto

```bash
cd ~/tools
git clone git://git.yoctoproject.org/poky
cd poky
git checkout -t origin/kirkstone -b kirkstone
git pull
```

Inicializar el build:
```bash
source oe-init-build-env rpi-build
```
6. Agregar capa de Raspberry Pi

```bash
cd ~/tools/poky
git clone https://git.yoctoproject.org/meta-raspberrypi
cd meta-raspberrypi/
git checkout -t origin/kirkstone -b kirkstone
git pull
```
7. Agregar capa de Tensorflow-lite

```bash
cd ~/tools/poky
git clone https://git.yoctoproject.org/meta-tensorflow
cd meta-tensorflow/
git checkout -t origin/kirkstone -b kirkstone
git pull
```
8. Agregar capa de Openembedded

```bash
cd ~/tools/poky
git clone https://github.com/openembedded/meta-openembedded.git
cd meta-openembedded/
git checkout -t origin/kirkstone -b kirkstone
git pull
```

Registrar la capa en bblayers.conf:
```bash
cd ~/tools/poky/rpi-build
bitbake-layers add-layer ../meta-raspberrypi
bitbake-layers add-layer ../meta-openembedded/meta-oe
bitbake-layers add-layer ../meta-openembedded/meta-python
bitbake-layers add-layer ../meta-openembedded/meta-networking
bitbake-layers add-layer ../meta-tensorflow
```

8. Configuración de compilación para Raspberry Pi 5

Editar conf/local.conf:
```bash
cd ~/tools/poky/rpi-build/
nano conf/local.conf
```

Modificar dentro de local.conf estas entradas, descomentalas o agregalas si no se encuentran
```bash

LICENSE_FLAGS_ACCEPTED = "commercial"

MACHINE = "raspberrypi4-64"
ENABLE_UART = "1"
GPU_MEM = "256"

MACHINE_FEATURES:append = " vc4graphics"
DISTRO_FEATURES:append = " x11 opengl"

#  KMS 
RPI_USE_KMS = "1"

```
Opciones de mirroring y hashserv (opcional):
```bash
BB_HASHSERVE_UPSTREAM = "hashserv.yoctoproject.org:8686"
SSTATE_MIRRORS ?= "file://.* http://sstate.yoctoproject.org/all/PATH;downloadfilename=PATH"
```


9. Importar receta custom.
Para importar la receta custom de nuestro semáforo, copiaremos el contenido de la carpeta meta-rpi-semaforo que se encuentra dentro de este repositorio <br>
Copie la carpeta meta-rpi-semaforo en ~/tools/poky <br>
Registrar la capa en bblayers.conf:
```bash
cd ~/tools/poky/rpi-build
bitbake-layers add-layer ../meta-rpi-semaforo
```

10. Descarga de dependencias para imagen mínima (opcional), para compilar offline

```bash
bitbake core-image-minimal -c fetch


```
11. Compilación de imagen mínima 

```bash
bitbake core-image-minimal
```

12. Generación y copia de imagen en la SD de la Raspberry pi4
La ruta donde va a estar la imagen compilada es la siguiente

```bash
cd ~/tools/poky/rpi-build/tmp/deploy/images/
```

13. Para flashearlo en Linux

Conecte e identifique la SD conectada en el equipo Linux:

```bash
lsblk
```
Luego ejecuta:
```bash
sudo umount /dev/sdx
```
Se elimina todo lo de la memoria para crear la imagen

```bash
sudo wipefs -a /dev/sdx
```

```bash
sudo bmaptool copy <image file>.rootfs.wic.bz2 --bmap <image file>.rootfs.wic.bmap /dev/sdX
```

Reemplaza sdX por el dispositivo (por ejemplo sda).
<image file> reemplazar por el nombre real del archivo. (por ejemplo core-image-minimal)

Cuando termine:
```bash
sudo eject /dev/sdX
```

La SD después del flasheo tendrá estas particiones:

    Partición: boot
    Sistema: FAT32
    Contenido: Image, *.dtb, config.txt, firmware
    
    Partición: rootfs
    Sistema: ext4/ext3
    Contenido: rootfs completo de Yocto

Listo, ya puede conectar la SD en la RaspberryPi 4 y ejecutar la imagen compilada.

Las credenciales por defecto son:

    User: root
    Pass: (vacío)

Referencias

[Site] https://docs.yoctoproject.org/ref-manual/system-requirements.html

[Site] https://git.yoctoproject.org/meta-raspberrypi/

[Site] https://docs.yoctoproject.org/brief-yoctoprojectqs/

[Site] https://github.com/agherzan/meta-raspberrypi

[Site] https://velog.io/@mythos/Yocto-Linux-Quick-Build-for-Raspberry-Pi-3B-Fedora-35
