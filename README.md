# PySyncDroid
PySyncDroid is a Python 2.7 powered CLI tool providing a simple way to synchronize an Android device connected to a Linux PC via MTP over USB.

## System requirements
PySyncDroid leverages `gvfs` and `mtp`.

### gvfs
Here is a list of gvfs related packages I have installed on my system (Ubuntu 14.04 64b):
``` bash
dm@Z580:~$ dpkg --get-selections | grep gvfs
gvfs:amd64					    install
gvfs-backends					install
gvfs-bin					    install
gvfs-common					    install
gvfs-daemons					install
gvfs-fuse					    install
gvfs-libs:amd64					install
```
Utilities as:
 * gvfs-ls
 * gvfs-cp
 * gvfs-rm
 * gvfs-mkdir
 
*must* be present on your system and executable from the terminal.

### mtp
Here is a list of mtp related packages I have installed on my system (Ubuntu 14.04 64b):
``` bash
dm@Z580:~$ dpkg --get-selections | grep mtp
libmtp-common					install
libmtp-runtime					install
libmtp9:amd64					install
```

## Installation
Run following commands in your terminal to download, extract and install PySyncDroid:
``` bash
cd ~/Downloads
wget https://github.com/DusanMadar/PySyncDroid/archive/master.zip -O PySyncDroid.zip
unzip PySyncDroid.zip
cd PySyncDroid-master/
python setup.py install
```
## Usage
1. Connect your Android device with an USB cable to your computer
2. Unlock your device to notify the computer about its presence
    * unlock is conducted only once and it is **not necessary** that the device stays unlocked during the synchronizing process
3. Make sure the device is connected as a **Media device (MTP)**
   * you should now be able to see your device in the *computer file manager*
4. Synchronize using PySyncDroid

### Examples
For more details about how to use PySyncDroid and what options are available
``` bash
pysyncdroid -h
```
Synchronize contents of the *Rock* directory from computer to the device
``` bash
dm@Z580:~/Desktop$ pysyncdroid -V samsung -M gt-i9300 -s /home/dm/Music/Rock -d Card/Music/Rock
```
Synchronize contents of the *Music* directory from the device to computer, removing unmatched files (i.e. files, which are present only on computer, but not on the device) and overwriting existing files.
Child derictories will be automaticaly created in the destination directory (*~/Music*, in this case) as necessary.
``` bash
dm@Z580:~$ pysyncdroid -V samsung -M gt-i9300 -s Phone/Music -d Music -o -u remove
```

## Limitations
* `source` and `destination` must be a path to a **directory**
* `single file` synchronization is **not supported**
* `computer path` **expansion** (resolving "`~`", "`..`", ...) is **not supported**; use absolute paths or relative paths to a child directory from the current working directory
* `device path` must be a relative path starting with one of the device directories visible in the computer file manager, e.g.:
    * *Card/Music*
    * *Phone/DCIM*
    * *Tablet/Download*
