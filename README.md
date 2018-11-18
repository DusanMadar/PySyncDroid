[![Build Status](https://travis-ci.org/DusanMadar/PySyncDroid.svg?branch=master)](https://travis-ci.org/DusanMadar/PySyncDroid)
[![Coverage Status](https://coveralls.io/repos/github/DusanMadar/PySyncDroid/badge.svg?branch=master)](https://coveralls.io/github/DusanMadar/PySyncDroid?branch=master)
[![PyPI version](https://badge.fury.io/py/pysyncdroid.svg)](https://badge.fury.io/py/pysyncdroid)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

# PySyncDroid
PySyncDroid is a Python 3 powered CLI tool providing a simple way to synchronize an Android device connected to a Linux PC via MTP over USB.

No special setup is required for the Android device.

## System requirements
PySyncDroid leverages `lsusb`, `gvfs`, `mtp` and `readlink`.

### lsusb
Make sure you have `lsusb` installed on your computer as it is used to discover USB connected devices.

### gvfs
Here is a list of gvfs related packages I have installed on my system (Ubuntu 14.04 64b):
``` bash
dm@Z580:~$ dpkg --get-selections | grep gvfs
gvfs:amd64             install
gvfs-backends          install
gvfs-bin               install
gvfs-common            install
gvfs-daemons           install
gvfs-fuse              install
gvfs-libs:amd64        install
```
Utilities as:
 * gvfs-ls
 * gvfs-cp
 * gvfs-rm
 * gvfs-mkdir
 * gvfs-mount

*must* be present on your system and executable from the terminal.

### mtp
Here is a list of mtp related packages I have installed on my system (Ubuntu 14.04 64b):
``` bash
dm@Z580:~$ dpkg --get-selections | grep mtp
libmtp-common          install
libmtp-runtime         install
libmtp9:amd64          install
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
    * `Developer Options` don't have to be enabled on the device
3. Make sure the device is connected as a **Media device (MTP)**
   * you should now be able to see your device in *computer file manager*
4. Synchronize using PySyncDroid

### Examples
For more details about how to use PySyncDroid and what options are available
``` bash
dm@Z580:~/Desktop$ pysyncdroid -h
```
Synchronize contents of the *Rock* directory from computer to the device (`vendor` and `model` names are *case insensitive*)
``` bash
dm@Z580:~/Desktop$ pysyncdroid -V samsung -M gt-i9300 -s ~/Music/Rock -d Card/Music/Rock
```
Synchronize contents of the *Music* directory from the device to computer, removing unmatched files (i.e. files, which are present only on computer, but not on the device) and overwriting existing files. Also, display what is going on (notice the `-v` flag).
Child directories are automaticaly created in the destination directory (*~/Music*, in this case) as necessary.
``` bash
dm@Z580:~$ pysyncdroid -ov -V samsung -M gt-i9300 -s Phone/Music -d Music -u remove
```

Provide a mapping file (see `src2dest_example.txt` for the file structure) if you need to synchronize more than a single directory.
``` bash
dm@Z580:~/Desktop$ pysyncdroid -V samsung -M gt-i9300 -f /home/dm/Desktop/src2dest_example.txt -v
```

### Device not found error
If you keep getting the following error message `Device "<vendor> <model>" not found` make sure the device is connected to the computer and you can access it via file manager.
Run `lsusb` and check the output for desired `vendor` or `model` names. For example, I get the following string for my Samsung Galaxy SIII `Bus 001 Device 011: ID 04e8:6860 Samsung Electronics Co., Ltd GT-I9100 Phone [Galaxy S II], GT-I9300 Phone [Galaxy S III], GT-P7500 [Galaxy Tab 10.1]` and therefore I use `PySyncDroid` as `pysyncdroid -V samsung -M gt-i9300`.

## Limitations & known issues
* `source` and `destination` must be a path to a **directory**
* `single file` synchronization is **not supported**
* `device path` must be a **relative path** starting with one of the device directories visible in the computer file manager, e.g.:
    * *Card/Music*
    * *Phone/DCIM*
    * *Tablet/Download*

### Sync from computer to device
If the sync process takes a bit longer (10+ minutes), it's very likely that you will get an error like:
`The name :<name> was not provided by any .service files` or `Message did not receive a reply (timeout by message bus)`.

It seems like *the device drops the MTP connection* after a certain amount of time/certaing amount of data transfered. Resetting USB connection (remove and plug the cable back to your computer) and unlocking the device again will reconnect it so you can re-run the last `pysyncdroid` command. It will continue to sync where it left off (assuming you are not using the `-o` flag).
