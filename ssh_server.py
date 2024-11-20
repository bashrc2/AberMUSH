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
        self.username = username
        self.password = password
        return paramiko.AUTH_SUCCESSFUL

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
    chan.sendall("Connected...\n")
    parent._id = parent.get_next_id()
    curr_id = parent._id
    parent.add_new_player(parent._CLIENT_SSH, chan, chan,
                          server.username, server.password)
    # clear any credentials
    server.username = server.password = None
    while 1:
        command = chan.recv(4096)

        if not t.is_active() or command in (b'exit\n', b'quit\n'):
            parent.handle_disconnect(curr_id)
            chan.shutdown(2)
            chan.close()
            break

        try:
            if curr_id >= 0:
                message = command.decode('utf-8').strip()
                parent.receive_message(curr_id, message)
        except KeyboardInterrupt as kexc:
            print('KeyboardInterrupt: ' + str(kexc))
            parent.handle_disconnect(curr_id)
            chan.shutdown(2)
            chan.close()
            break
        except subprocess.CalledProcessError:
            chan.sendall(b'Unknown command: ' + command)
        except OSError as kexc:
            print('OSError: ' + str(kexc))
            parent.handle_disconnect(curr_id)
            chan.shutdown(2)
            chan.close()
            break
    time.sleep(1)


def ssh_listen_for_connections(sock, host_key, parent) -> None:
    """Listens for incoming ssh connections
    """
    while 1:
        try:
            client, _ = sock.accept()
        except BaseException as exc:
            print('EX: ssh_listen_for_connections accept ' + str(exc))
            break

        print('Got a connection!')

        chan = None
        curr_id = parent.get_next_id()
        started = False
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

            server.parent = parent

            chan = t.accept(20)
            conn_handler = \
                threading.Thread(target=handle_ssh_connection,
                                 args=(t, chan, parent, server,))
            conn_handler.start()
            started = True

        except EOFError as exc4:
            print('EX: ssh_listen_for_connections EOFError 1 ' + str(exc4))
            try:
                if started:
                    parent.handle_disconnect(curr_id)
                if chan:
                    chan.shutdown(2)
                    chan.close()
            except BaseException as exc3:
                print('EX: ssh_listen_for_connections EOFError 2 ' +
                      str(exc3))
                pass
            continue
        except OSError as exc2:
            print("Exit: " + str(exc2))
            try:
                if started:
                    parent.handle_disconnect(curr_id)
                if chan:
                    chan.shutdown(2)
                    chan.close()
            except BaseException as exc3:
                print('EX: ssh_listen_for_connections OSError ' + str(exc3))
                pass
            break

        time.sleep(3)


def run_ssh_server(domain: str, ssh_port: int, parent) -> None:
    """Runs an ssh server
    """
    host_key_filename = './.ssh_rsa_mud'
    host_key = None
    try:
        host_key = paramiko.RSAKey(filename=host_key_filename)
    except FileNotFoundError:
        print('Generating SSH server host key')

    if not host_key:
        host_key = paramiko.RSAKey.generate(bits=2048)
        host_key.write_private_key_file(host_key_filename)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((domain, ssh_port))
        sock.listen(100)
        print('SSH server created on port ' + str(ssh_port))
    except BaseException as exc:
        print('*** SSH server creation failed: ' + str(exc))
        return None

    conn_listener = \
        threading.Thread(target=ssh_listen_for_connections,
                         args=(sock, host_key, parent,))
    conn_listener.start()
