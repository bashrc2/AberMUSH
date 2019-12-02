__filename__ = "gcos.py"
__author__ = "Bob Mottram"
__credits__ = ["Bartek Radwanski", "Mark Frimston"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@freedombone.net"
__status__ = "Production"

import os

def terminalEmulator(command: str,mud,id) -> bool:
    """ easteregg
    A completely convincing Honeywell emulator
    """
    command=command.strip().lower()

    if command=='ls' or command.startswith('ls ') or \
       command=='dir' or command.startswith('dir '):
        mud.send_message(
            id, "<f220>drwxr-xr-x 105   09:41 README.TXT")
        mud.send_message(
            id, "\n<f220>drwxr-xr-x 92387 12:17 SPOOL")
        mud.send_message(
            id, "\n<f220>drwxr-xr-x 92387 12:17 TELNET/")
        mud.send_message(
            id, "\n<f220>drwxr-xr-x 7252  09:48 USERS.TXT")
        mud.send_message(
            id, "\n>")
        return True        

    if command.startswith('mkdir') or \
       command.startswith('rm ') or \
       command.startswith('rmdir ') or \
       command.startswith('echo '):
        mud.send_message(
            id, "<f220>OK")
        mud.send_message(
            id, "\n>")
        return True        

    if command.startswith('telnet'):
        mud.send_message(
            id, "<f220>Connected to tape drive 0")
        mud.send_message(
            id, "\n<f220>Escape character is '^]'.")
        mud.send_message(
            id, "\n>")
        return True        
    
    if command=='cat' or command=='chown':
        mud.send_message(
            id, "<f220>LOAD TAPE DRIVE")
        mud.send_message(
            id, "\n>")
        return True        

    if command.startswith('mount ') or command=='mount':
        mud.send_message(
            id, "<f220>TAPE DRIVE MOUNTED")
        mud.send_message(
            id, "\n>")
        return True        

    if command.startswith('shred ') or command=='dd' or command.startswith('dd '):
        mud.send_message(
            id, "<f220>TAPE DRIVE ERROR 7291")
        mud.send_message(
            id, "\n>")
        return True

    if command.startswith('chmod'):
        mud.send_message(
            id, "<f220>CONFIRMED")
        mud.send_message(
            id, "\n>")
        return True

    if command=='pwd' or command.startswith('dirname'):
        mud.send_message(
            id, "<f220>/HOME/CORMORANT")
        mud.send_message(
            id, "\n>")
        return True

    if command=='uname' or command.startswith('arch '):
        mud.send_message(
            id, "<f220>GCOS TSS")
        mud.send_message(
            id, "\n>")
        return True

    if command.startswith('useradd') or command.startswith('adduser'):
        mud.send_message(
            id, "<f220>REWIND TAPE")
        mud.send_message(
            id, "\n>")
        return True        

    invalidNames=("sh","bash","chcon","chgrp","chown","chmod","cp","cd","dd","df","dir","dircolors","install","ln","ls","mkdir","mkfifo","mknod","mktemp","mv","realpath","rm","rmdir","shred","sync","touch","truncate","vdir","b2sum","base32","base64","cat","cksum","comm","csplit","cut","expand","fmt","fold","head","join","md5sum","nl","numfmt","od","paste","ptx","pr","sha1sum","sha224sum","sha256sum","sha384sum","sha512sum","shuf","sort","split","sum","tac","tail","tr","tsort","unexpand","uniq","wc","arch","basename","chroot","date","dirname","du","echo","env","expr","factor","false","groups","hostid","id","link","logname","nice","nohup","nproc","pathchk","pinky","printenv","printf","pwd","readlink","runcon","seq","sleep","stat","stdbuf","stty","tee","test","timeout","true","tty","uname","unlink","uptime","users","useradd","adduser","who","whoami","yes")
    if command in invalidNames:
        mud.send_message(
            id, "\n<f220>GCOS-3 TSS Aberystwyth Computing Research Centre (Channel d.h000)")
        mud.send_message(
            id, "\n<f220>Load = 7.0 out of 90.0 units: users = 7, 14/07/1989  1531.6 gmt Sun")
        mud.send_message(
            id, "\n<f220>You are protected from preemption.")
        mud.send_message(
            id, "\n<f220>Logged in from ASCII terminal \"cormorant\"")
        mud.send_message(
            id, "\n\n<f220>New messages in message_of_the_day:")
        mud.send_message(
            id, "\n\n<f220>Welcome to the GCOS System.")
        mud.send_message(id, "\n\n>")

        return True
    return False
