__filename__ = "gcos.py"
__author__ = "Bob Mottram"
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@libreserver.org"
__status__ = "Production"
__module_group__ = "Mainframe Emulator"


def _terminal_mount(mud, id) -> None:
    """Mount
    """
    mud.send_message(id, "<f220>DSS port C mounted")
    mud.send_message(id, "\n>")


def terminal_emulator(command: str, params: str, mud, id) -> bool:
    """ easteregg
    A completely convincing Honeywell emulator
    """
    command = command.strip().lower()

    if 'while' in params:
        mud.send_message(id, "skip_bytesfullblockbscountseekskipifofsta" +
                         "tusibsobsconviflagoflagseek_bytesnonenoxferwr" +
                         "itingarchiveaforcefinteractivecatapultilinkld" +
                         "ereferenceLno-dereferencePrecursiveRsymbolic")
        mud.send_message(id, "usage: printf FORMAT")
        mud.send_message(id, "bad field specification")
        mud.send_message(id, "\n>")
        return True

    if command in ('ls', 'dir'):
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

    if command in ('mkdir', 'rm', 'rmdir', 'echo'):
        mud.send_message(id, "<f220>OK")
        mud.send_message(id, "\n>")
        return True

    if command in ('passwd', 'pass'):
        mud.send_message(id, "<f220>New password:")
        mud.send_message(id, "\n>")
        return True

    if command in ('telnet', "telnetadmin", "admin", "linuxshell", "root"):
        mud.send_message(id, "<f220>Connected to DSS port C")
        mud.send_message(id, "\n<f220>Datanet 1200 open")
        mud.send_message(id, "\n>")
        return True

    if command == 'chown':
        mud.send_message(id, "<f220>Load DSS port C")
        mud.send_message(id, "\n>")
        return True

    if command == 'cat':
        if ';' not in params:
            mud.send_message(
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
            mud.send_message(id, "\n>")
            return True
        if 'mount' in params:
            _terminal_mount(mud, id)
            mud.send_message(id, "portc /spc spcfs rw 0 0")
            mud.send_message(id, "proc /proc proc rw 0 0")
            mud.send_message(id, "\n>")
            return True
        if 'busybox' in params:
            params = params.split('busybox', 1)[1]
            command = 'busybox'
        else:
            mud.send_message(id, "cat: Invalid DSS port")
            mud.send_message(id, "\n>")
            return True

    if command in ('unmount', 'umount'):
        mud.send_message(id, "<f220>DSS port C spindown")
        mud.send_message(id, "\n>")
        return True

    if command == 'mount':
        _terminal_mount(mud, id)
        return True

    if command in ('shred ', 'dd'):
        mud.send_message(id, "<f220>ERROR 7291")
        mud.send_message(id, "\n>")
        return True

    if command == 'chmod':
        mud.send_message(id, "<f220>Confirmed")
        mud.send_message(id, "\n>")
        return True

    if command in ('pwd', 'dirname'):
        mud.send_message(id, "<f220>/udd/acrc/cormorant")
        mud.send_message(id, "\n>")
        return True

    if command == 'whoami':
        mud.send_message(id, "<f220>cormorant")
        mud.send_message(id, "\n>")
        return True

    if command == 'who':
        mud.send_message(id, "<f220>amsys")
        mud.send_message(id, "<f220>blackbird")
        mud.send_message(id, "<f220>cormorant")
        mud.send_message(id, "<f220>greenman")
        mud.send_message(id, "<f220>solo")
        mud.send_message(id, "<f220>titan2")
        mud.send_message(id, "<f220>vulcan")
        mud.send_message(id, "\n>")
        return True

    if command == 'nmap':
        mud.send_message(id, "<f220>Press START")
        mud.send_message(id, "\n>")
        return True

    if command in ('shutdown', 'reset'):
        mud.send_message(id, "<f220>DSS port A spindown")
        mud.send_message(id, "<f220>DSS port C spindown")
        mud.send_message(id, ">")
        return True

    if command in ('uname', 'arch'):
        mud.send_message(id, "<f220>GCOS-3 TSS")
        mud.send_message(id, "\n>")
        return True

    if command in ('who', 'whoami', 'whois'):
        mud.send_message(id, "<f220>cormorant")
        mud.send_message(id, "<f220>Data Services Division. Room 5A")
        mud.send_message(id, "<f220>Aberystwyth Computing Research Centre")
        mud.send_message(id, "\n>")
        return True

    if command in ('useradd', 'adduser'):
        mud.send_message(id, "<f220>Rewind DSS port B")
        mud.send_message(id, "\n>")
        return True

    if command == 'printf':
        mud.send_message(id, "<f220>DSS port B interlace enabled")
        mud.send_message(id, "\n>")
        return True

    if command == 'sh':
        mud.send_message(id, "BusyBox v1.24 () built-in shell (ash)")
        mud.send_message(id, "\n>")
        return True

    if command == 'wget':
        mud.send_message(id, "100%[=========================================" +
                         "==================================================" +
                         "==>]   1.41K  --.-KB/s    in 1s")
        mud.send_message(id, "1989-12-08 10:39:10 (1 KB/s) - " +
                         "saved to DSS port A [232/232]")
        mud.send_message(id, "\n>")
        return True

    invalid_names = (
        "sh", "bash", "chcon", "chgrp", "chown", "chmod", "cp",
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
        "busybox", "/bin/bash", "bash", "/bin/sh", "bin",
        "root"
    )
    if command in invalid_names:
        mud.send_message(id, "<f220>System GCOS3 MOD400 - S104 -0714/1417")
        mud.send_message(id, "<f220>Aberystwyth Computing " +
                         "Research Group ready!")
        mud.send_message(id,
                         "<f220>Logged in from DLCP terminal \"cormorant\"")
        if params:
            possible_shells = {
                "/bin/busybox": "VAR: applet not found",
                "/bin/sh": "BusyBox v1.24 () built-in shell (ash)",
                "/bin/bash": "/bin/bash: VAR: No such file or directory"
            }
            for poss_shell, shell_response in possible_shells.items():
                if poss_shell in params:
                    shell_param = params.split(poss_shell, 1)[1].strip()
                    shell_response = shell_response.replace('VAR', shell_param)
                    mud.send_message(id, "\n>" + poss_shell + ' ' +
                                     shell_param)
                    mud.send_message(id, "\n" + shell_response)
                    mud.send_message(id, "\n>")
                    return True
        mud.send_message(id, "\n>")
        return True

    return False
