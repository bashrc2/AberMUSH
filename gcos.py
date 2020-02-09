__filename__ = "gcos.py"
__author__ = "Bob Mottram"
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@freedombone.net"
__status__ = "Production"

import os

def terminalEmulator(command: str,params: str,mud,id) -> bool:
    """ easteregg
    A completely convincing Honeywell emulator
    """
    command=command.strip().lower()

    if command=='ls' or command=='dir':
        mud.send_message(id, "<f220>.")
        mud.send_message(id, "<f220>..")
        mud.send_message(
            id, "<f220>drwxr-xr-x 105   09:41 am/")
        mud.send_message(
            id, "<f220>drwxr-xr-x 105   09:41 ddd/")
        mud.send_message(
            id, "<f220>drwxr-xr-x 105   09:41 gdd/")
        mud.send_message(
            id, "<f220>drwxr-xr-x 105   09:41 pdd/")
        mud.send_message(
            id, "<f220>drwxr-xr-x 105   09:41 sci/")
        mud.send_message(
            id, "<f220>drwxr-xr-x 105   09:41 sss/")
        mud.send_message(
            id, "<f220>drwxr-xr-x 105   09:41 udd/")
        mud.send_message(id, "\n>")
        return True        

    if command=='mkdir' or \
       command=='rm' or \
       command=='rmdir' or \
       command=='echo':
        mud.send_message(id, "<f220>OK")
        mud.send_message(id, "\n>")
        return True        

    if command=='passwd' or command=='pass':
        mud.send_message(id, "<f220>New password:")
        mud.send_message(id, "\n>")
        return True

    if command=='telnet':
        mud.send_message(id, "<f220>Connected to tape drive 0")
        mud.send_message(id, "\n<f220>Datanet 1200 open")
        mud.send_message(id, "\n>")
        return True        
    
    if command=='chown':
        mud.send_message(id, "<f220>Load tape drive")
        mud.send_message(id, "\n>")
        return True        

    if command=='cat' and ';' not in params:
        mud.send_message(id, "<f220>There is a fair fort upon the sea-shore.\nPleasantly, each is given his desire.\nAsk Gwynedd, let it be yours.\nRough, stiff spears they earned.\nOn Wednesday, I saw men in conflict;\non Thursday, it was reproaches they contended with.\nAnd hair was red with blood, and lamenting on harps.\nWeary were the men of Gwynedd the day they came,\nand atop the stone of Maelwy they shelter shields.\nA host of kinsmen fell by the descendant.")
        mud.send_message(id, "\n>")
        return True        

    if command=='unmount':
        mud.send_message(id, "<f220>Tape drive 1 spinup")
        mud.send_message(id, "\n>")
        return True

    if command=='mount':
        mud.send_message(id, "<f220>Tape drive 1 mounted")
        mud.send_message(id, "\n>")
        return True        

    if command=='shred ' or command=='dd':
        mud.send_message(id, "<f220>ERROR 7291")
        mud.send_message(id, "\n>")
        return True

    if command=='chmod':
        mud.send_message(id, "<f220>Confirmed")
        mud.send_message(id, "\n>")
        return True

    if command=='pwd' or command=='dirname':
        mud.send_message(id, "<f220>/udd/acrc/cormorant")
        mud.send_message(id, "\n>")
        return True

    if command=='whoami':
        mud.send_message(id, "<f220>cormorant")
        mud.send_message(id, "\n>")
        return True

    if command=='who':
        mud.send_message(id, "<f220>amsys")
        mud.send_message(id, "<f220>blacksmith")
        mud.send_message(id, "<f220>cormorant")
        mud.send_message(id, "<f220>greenman")
        mud.send_message(id, "<f220>solo")
        mud.send_message(id, "<f220>titan2")
        mud.send_message(id, "<f220>vulcan")
        mud.send_message(id, "\n>")
        return True

    if command=='nmap':
        mud.send_message(id, "<f220>Press START")
        mud.send_message(id, "\n>")
        return True

    if command=='shutdown' or command=='reset':
        mud.send_message(id, "<f220>Tape drive 0 spindown")
        mud.send_message(id, "<f220>Tape drive 1 spindown")
        mud.send_message(id, ">")
        return True

    if command=='uname' or command=='arch':
        mud.send_message(id, "<f220>GCOS-3 TSS")
        mud.send_message(id, "\n>")
        return True

    if command=='who' or command=='whoami' or command=='whois':
        mud.send_message(id, "<f220>cormorant")
        mud.send_message(id, "<f220>Data Services Division. Room 5A")
        mud.send_message(id, "<f220>Aberystwyth Computing Research Centre")
        mud.send_message(id, "\n>")
        return True

    if command=='useradd' or command=='adduser':
        mud.send_message(id, "<f220>Rewind tape drive 1")
        mud.send_message(id, "\n>")
        return True

    if command=='wget':
        mud.send_message(id, "100%[=============================================================================================>]   1.41K  --.-KB/s    in 1s")
        mud.send_message(id, "1989-12-08 10:39:10 (1 KB/s) - saved to tape 0 [232/232]")
        mud.send_message(id, "\n>")        
        return True

    invalidNames=("sh","bash","chcon","chgrp","chown","chmod","cp","cd","dd","df","dir","dircolors","install","ln","ls","mkdir","mkfifo","mknod","mktemp","mv","realpath","rm","rmdir","shred","sync","touch","truncate","vdir","b2sum","base32","base64","cat","cksum","comm","csplit","cut","expand","fmt","fold","head","join","md5sum","nl","numfmt","od","paste","ptx","pr","sha1sum","sha224sum","sha256sum","sha384sum","sha512sum","shuf","sort","split","sum","tac","tail","tr","tsort","unexpand","uniq","wc","arch","basename","chroot","date","dirname","du","echo","env","expr","factor","false","groups","hostid","id","link","logname","nice","nohup","nproc","pathchk","pinky","printenv","printf","pwd","readlink","runcon","seq","sleep","stat","stdbuf","stty","tee","test","timeout","true","tty","uname","unlink","uptime","users","useradd","adduser","yes","/bin/busybox","busybox","/bin/bash","bash","/bin/sh")
    if command in invalidNames:
        mud.send_message(id, "<f220>System GCOS3 MOD400 - S104 -0714/1417")
        mud.send_message(id, "<f220>Aberystwyth Computing Research Group ready!")
        mud.send_message(id, "<f220>Logged in from DLCP terminal \"cormorant\"")
        if params:
            possibleShells={
                "/bin/busybox": "VAR: applet not found",
                "/bin/sh": "/bin/sh: 0: Can't open VAR",
                "/bin/bash": "/bin/bash: VAR: No such file or directory"
            }
            for possShell,shellResponse in possibleShells.items():
                if possShell in params:
                    shellParam=params.split(possShell,1)[1].strip()
                    shellResponse=shellResponse.replace('VAR',shellParam)
                    mud.send_message(id, "\n>"+possShell+' '+shellParam)
                    mud.send_message(id, "\n"+shellResponse)
                    mud.send_message(id, "\n>")
                    return True
        mud.send_message(id, "\n>")
        return True

    return False
