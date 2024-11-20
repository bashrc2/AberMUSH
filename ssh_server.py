__filename__ = "ssh_server.py"
__author__ = "Bob Mottram"
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@libreserver.org"
__status__ = "Production"
__module_group__ = "Command Interface"

import paramiko
import threading
import socket
import subprocess
import time

ssh_user_accounts = {
    "admin": {
        "password": "admin"
    }
}


class SSHServer(paramiko.ServerInterface):
    """Implements a SSH server
    """
    def __init__(self):
        self.event = threading.Event()

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        if username in ssh_user_accounts:
            if password == ssh_user_accounts[username]['password']:
                return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def check_channel_pty_request(self, channel: paramiko.Channel, term: bytes,
                                  width: int, height: int, pixelwidth: int,
                                  pixelheight: int, modes: bytes) -> bool:
        return False

    def check_channel_shell_request(self, channel: paramiko.Channel) -> bool:
        return True

    def check_channel_exec_request(self, channel: paramiko.Channel,
                                   command) -> bool:
        print('command: ' + str(command))
        return True


def handle_ssh_connection(t, chan, parent, server):
    """Handles an incoming ssh connection
    """
    if not chan:
        return
    chan.send("Connected...\n")
    parent._id = parent.get_next_id()
    parent.add_new_player(parent._CLIENT_SSH, chan, chan)
    while 1:
        command = chan.recv(4096)
        if len(command) > 0:
            print('handle_ssh_connection: ' + str(command))

        if command in (b'exit\n', b'quit\n'):
            print('Exit')
            chan.send("Bye\n")
            parent.handle_disconnect(parent._id)
            chan.close()
            break

        try:
            if parent._id >= 0:
                message = command.decode('utf-8').strip()
                parent.receive_message(parent._id, message)
        except KeyboardInterrupt as kexc:
            print('KeyboardInterrupt: ' + str(kexc))
            parent.handle_disconnect(parent._id)
            chan.close()
        except subprocess.CalledProcessError:
            chan.send(b'Unknown command: ' + command)
        except OSError:
            parent.handle_disconnect(parent._id)
            chan.close()
            break


def ssh_listen_for_connections(sock, host_key, parent) -> None:
    """Listens for incoming ssh connections
    """
    while 1:
        try:
            client, _ = sock.accept()
        except BaseException:
            continue

        print('Got a connection!')

        chan = None
        try:
            t = paramiko.Transport(client)
            t.add_server_key(host_key)
            paramiko.util.log_to_file("ssh_log.txt")
            server = SSHServer()
            try:
                t.start_server(server=server)
            except paramiko.SSHException:
                print('SSH negotiation failed')
                return

            chan = t.accept(20)
            conn_handler = \
                threading.Thread(target=handle_ssh_connection,
                                 args=(t, chan, parent, server,))
            conn_handler.start()

        except EOFError:
            try:
                chan.close()
            except BaseException:
                pass
            continue
        except OSError as exc2:
            print("Exit: " + str(exc2))
            try:
                chan.close()
            except BaseException:
                pass
            break

        time.sleep(3)


def run_ssh_server(domain: str, ssh_port: int, parent) -> None:
    """Runs an ssh server
    """
    host_key = None
    try:
        host_key = paramiko.RSAKey(filename='./rsa_mud')
    except FileNotFoundError:
        print('Generating server key')

    if not host_key:
        host_key = paramiko.RSAKey.generate(bits=2048)
        host_key.write_private_key_file('./rsa_mud')

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((domain, ssh_port))
        sock.listen(100)
        print('Listening for connection ...')
    except BaseException as exc:
        print('*** Listen/accept failed: ' + str(exc))
        return None

    conn_listener = \
        threading.Thread(target=ssh_listen_for_connections,
                         args=(sock, host_key, parent,))
    conn_listener.start()
