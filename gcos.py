__filename__ = "gcos.py"
__author__ = "Bob Mottram"
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@libreserver.org"
__status__ = "Production"
__module_group__ = "Mainframe Emulator"


def _terminalMount(mud, id):
    mud.sendMessage(id, "<f220>DSS port C mounted")
    mud.sendMessage(id, "\n>")


def terminalEmulator(command: str, params: str, mud, id) -> bool:
    """ easteregg
    A completely convincing Honeywell emulator
    """
    command = command.strip().lower()

    if 'while' in params:
        mud.sendMessage(id, "skip_bytesfullblockbscountseekskipifofsta" +
                        "tusibsobsconviflagoflagseek_bytesnonenoxferwr" +
                        "itingarchiveaforcefinteractivecatapultilinkld" +
                        "ereferenceLno-dereferencePrecursiveRsymbolic")
        mud.sendMessage(id, "usage: printf FORMAT")
        mud.sendMessage(id, "bad field specification")
        mud.sendMessage(id, "\n>")
        return True

    if command == 'ls' or command == 'dir':
        mud.sendMessage(id, "<f220>.")
        mud.sendMessage(id, "<f220>..")
        mud.sendMessage(
            id, "<f220>drwxr-xr-x 105   09:41 am/")
        mud.sendMessage(
            id, "<f220>drwxr-xr-x 105   09:41 ddd/")
        mud.sendMessage(
            id, "<f220>drwxr-xr-x 105   09:41 gdd/")
        mud.sendMessage(
            id, "<f220>drwxr-xr-x 105   09:41 pdd/")
        mud.sendMessage(
            id, "<f220>drwxr-xr-x 105   09:41 sci/")
        mud.sendMessage(
            id, "<f220>drwxr-xr-x 105   09:41 sss/")
        mud.sendMessage(
            id, "<f220>drwxr-xr-x 105   09:41 udd/")
        mud.sendMessage(id, "\n>")
        return True

    if command == 'mkdir' or \
       command == 'rm' or \
       command == 'rmdir' or \
       command == 'echo':
        mud.sendMessage(id, "<f220>OK")
        mud.sendMessage(id, "\n>")
        return True

    if command == 'passwd' or command == 'pass':
        mud.sendMessage(id, "<f220>New password:")
        mud.sendMessage(id, "\n>")
        return True

    if command == 'telnet':
        mud.sendMessage(id, "<f220>Connected to DSS port C")
        mud.sendMessage(id, "\n<f220>Datanet 1200 open")
        mud.sendMessage(id, "\n>")
        return True

    if command == 'chown':
        mud.sendMessage(id, "<f220>Load DSS port C")
        mud.sendMessage(id, "\n>")
        return True

    if command == 'cat':
        if ';' not in params:
            mud.sendMessage(
                id, "<f220>There is a fair fort upon the sea-shore." +
                "\nPleasantly, each is given his desire.\n" +
                "Ask Gwynedd, let it be yours.\nRough, stiff spears" +
                " they earned.\nOn Wednesday, I saw men in conflict" +
                ";\non Thursday, it was reproaches they contended " +
                "with.\nAnd hair was red with blood, and lamenting " +
                "on harps.\nWeary were the men of Gwynedd the day " +
                "they came,\nand atop the stone of Maelwy they " +
                "shelter shields.\nA host of kinsmen fell by the " +
                "descendant.")
            mud.sendMessage(id, "\n>")
            return True
        else:
            if 'mount' in params:
                _terminalMount(mud, id)
                mud.sendMessage(id, "portc /spc spcfs rw 0 0")
                mud.sendMessage(id, "proc /proc proc rw 0 0")
                mud.sendMessage(id, "\n>")
                return True
            if 'busybox' in params:
                params = params.split('busybox', 1)[1]
                command = 'busybox'
            else:
                mud.sendMessage(id, "cat: Invalid DSS port")
                mud.sendMessage(id, "\n>")
                return True

    if command == 'unmount' or command == 'umount':
        mud.sendMessage(id, "<f220>DSS port C spindown")
        mud.sendMessage(id, "\n>")
        return True

    if command == 'mount':
        _terminalMount(mud, id)
        return True

    if command == 'shred ' or command == 'dd':
        mud.sendMessage(id, "<f220>ERROR 7291")
        mud.sendMessage(id, "\n>")
        return True

    if command == 'chmod':
        mud.sendMessage(id, "<f220>Confirmed")
        mud.sendMessage(id, "\n>")
        return True

    if command == 'pwd' or command == 'dirname':
        mud.sendMessage(id, "<f220>/udd/acrc/cormorant")
        mud.sendMessage(id, "\n>")
        return True

    if command == 'whoami':
        mud.sendMessage(id, "<f220>cormorant")
        mud.sendMessage(id, "\n>")
        return True

    if command == 'who':
        mud.sendMessage(id, "<f220>amsys")
        mud.sendMessage(id, "<f220>blackbird")
        mud.sendMessage(id, "<f220>cormorant")
        mud.sendMessage(id, "<f220>greenman")
        mud.sendMessage(id, "<f220>solo")
        mud.sendMessage(id, "<f220>titan2")
        mud.sendMessage(id, "<f220>vulcan")
        mud.sendMessage(id, "\n>")
        return True

    if command == 'nmap':
        mud.sendMessage(id, "<f220>Press START")
        mud.sendMessage(id, "\n>")
        return True

    if command == 'shutdown' or command == 'reset':
        mud.sendMessage(id, "<f220>DSS port A spindown")
        mud.sendMessage(id, "<f220>DSS port C spindown")
        mud.sendMessage(id, ">")
        return True

    if command == 'uname' or command == 'arch':
        mud.sendMessage(id, "<f220>GCOS-3 TSS")
        mud.sendMessage(id, "\n>")
        return True

    if command == 'who' or command == 'whoami' or command == 'whois':
        mud.sendMessage(id, "<f220>cormorant")
        mud.sendMessage(id, "<f220>Data Services Division. Room 5A")
        mud.sendMessage(id, "<f220>Aberystwyth Computing Research Centre")
        mud.sendMessage(id, "\n>")
        return True

    if command == 'useradd' or command == 'adduser':
        mud.sendMessage(id, "<f220>Rewind DSS port B")
        mud.sendMessage(id, "\n>")
        return True

    if command == 'printf':
        mud.sendMessage(id, "<f220>DSS port B interlace enabled")
        mud.sendMessage(id, "\n>")
        return True

    if command == 'sh':
        mud.sendMessage(id, "BusyBox v1.24 () built-in shell (ash)")
        mud.sendMessage(id, "\n>")
        return True

    if command == 'wget':
        mud.sendMessage(id, "100%[=========================================" +
                        "==================================================" +
                        "==>]   1.41K  --.-KB/s    in 1s")
        mud.sendMessage(id, "1989-12-08 10:39:10 (1 KB/s) - " +
                        "saved to DSS port A [232/232]")
        mud.sendMessage(id, "\n>")
        return True

    invalidNames = ("sh", "bash", "chcon", "chgrp", "chown", "chmod", "cp",
                    "cd", "dd", "df", "dir", "dircolors", "install", "ln",
                    "ls", "mkdir", "mkfifo", "mknod", "mktemp", "mv",
                    "realpath", "rm", "rmdir", "shred", "sync", "touch",
                    "truncate", "vdir", "b2sum", "base32", "base64", "cat",
                    "cksum", "comm", "csplit", "cut", "expand", "fmt",
                    "fold", "head", "join", "md5sum", "nl", "numfmt",
                    "od", "paste", "ptx", "pr", "sha1sum", "sha224sum",
                    "sha256sum", "sha384sum", "sha512sum", "shuf", "sort",
                    "split", "sum", "tac", "tail", "tr", "tsort",
                    "unexpand", "uniq", "wc", "arch", "basename", "chroot",
                    "date", "dirname", "du", "echo", "env", "expr",
                    "factor", "false", "groups", "hostid", "id", "link",
                    "logname", "nice", "nohup", "nproc", "pathchk", "pinky",
                    "printenv", "printf", "pwd", "readlink", "runcon",
                    "seq", "sleep", "stat", "stdbuf", "stty", "tee", "test",
                    "timeout", "true", "tty", "uname", "unlink", "uptime",
                    "users", "useradd", "adduser", "yes", "/bin/busybox",
                    "busybox", "/bin/bash", "bash", "/bin/sh")
    if command in invalidNames:
        mud.sendMessage(id, "<f220>System GCOS3 MOD400 - S104 -0714/1417")
        mud.sendMessage(id, "<f220>Aberystwyth Computing " +
                        "Research Group ready!")
        mud.sendMessage(id,
                        "<f220>Logged in from DLCP terminal \"cormorant\"")
        if params:
            possibleShells = {
                "/bin/busybox": "VAR: applet not found",
                "/bin/sh": "BusyBox v1.24 () built-in shell (ash)",
                "/bin/bash": "/bin/bash: VAR: No such file or directory"
            }
            for possShell, shellResponse in possibleShells.items():
                if possShell in params:
                    shellParam = params.split(possShell, 1)[1].strip()
                    shellResponse = shellResponse.replace('VAR', shellParam)
                    mud.sendMessage(id, "\n>" + possShell + ' ' + shellParam)
                    mud.sendMessage(id, "\n" + shellResponse)
                    mud.sendMessage(id, "\n>")
                    return True
        mud.sendMessage(id, "\n>")
        return True

    return False
