Guía de compilación Yocto para Raspberry Pi 4

Entorno: RHEL 10 / Fedora 42 usando Toolbx o Podman 

1. Preparación del entorno

Instalación de Toolbox en un host Fedora / RHEL 10
```bash
sudo dnf install toolbox
```
Si desea usar Podman

```bash
sudo dnf -y install podman
```

Crear el directorio de trabajo:
```bash
mkdir ~/tools
```
2. Creación del contenedor

Usando Toolbox (recomendado):
```bash
toolbox create --image registry.fedoraproject.org/fedora-toolbox:38 yocto
```

Usando Podman:
```bash
podman run -it --name yocto -v /home/<user>/tools:/tools:z registry.fedoraproject.org/fedora-toolbox:38 /bin/bash
```

Notas:

    Reemplazar <user> por tu usuario.
    Dentro del contenedor, Toolbox mantiene rutas del host (~/tools), Podman las monta en /tools.

    Se utiliza la imagen de Fedora 40 como contenedor con un alias 'yocto'

3. Ingreso al contenedor

Usando Toolbox:
```bash
toolbox enter yocto
```

Usando Podman:
```bash
podman start -ai yocto
su - build
```

Consideraciones:

    En Podman se requiere un usuario sin privilegios de root (Yocto no permite compilar como root)

    En Toolbox esto no es necesario, ya que las carpetas del host están expuestas y se ejecuta con el usuario del sistema

Crear usuario no root en Podman:
```bash
useradd -m -u 1000 -s /bin/bash build
```
El usuario se llamará build.

4. Instalación de dependencias
   
Como root (Toolbox o Podman:
```bash
dnf install -y @development-tools bzip2 ccache chrpath cpio cpp diffstat diffutils file findutils gawk gcc gcc-c++ git glibc-devel glibc-langpack-en gzip hostname lz4 make patch perl perl-Data-Dumper perl-File-Compare perl-File-Copy perl-FindBin perl-Text-ParseWords perl-Thread-Queue perl-bignum perl-locale python python3 python3-devel python3-GitPython python3-jinja2 python3-pexpect python3-pip python3-setuptools rpcgen socat tar texinfo unzip wget which xz zstd SDL-devel xterm mesa-libGL-devel nano sudo
```

4. Configuración de idioma

```bash
dnf install -y glibc-all-langpacks
echo 'LANG=en_US.UTF-8' > /etc/locale.conf
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
```
Finalmente ya puede salir de root:

```bash
exit
```
Y volverá a usuario normal

En podman, requerimos entrar en modo usuario build:

```bash
su - build
```

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

8. Configuración de compilación para Raspberry Pi 4

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
