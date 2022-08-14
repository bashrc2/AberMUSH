__filename__ = "mudserver.py"
__author__ = "Bob Mottram"
__credits__ = ["Bartek Radwanski", "Mark Frimston",
               "Dave P. https://github.com/dpallot"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@libreserver.org"
__status__ = "Production"
__module_group__ = "Core"


"""Basic MUD server module for creating text-based Multi-User Dungeon
(MUD) games.

Contains one class, MudServer, which can be instantiated to start a
server running then used to send and receive messages from players.

author: Mark Frimston - mfrimston@gmail.com
"""

import signal
import socket
import select
import time
import sys
import ssl
import textwrap
from cmsg import cmsg
from WebSocketServer import WebSocket, WebSocketServer, tlsWebSocketServer
from threads import threadWithTrace
from functions import show_timing

ws_clients = []


class MudServerWS(WebSocket):
    _id = -1

    _CLIENT_WEBSOCKET = 2

    def handleMessage(self):
        # web interface sent a message
        # print('Player ' + str(self._id) + u' sent: ' + self.data)
        if self._id < 0:
            return
        self.server.parent.receive_message(self._id, self.data.strip())

    def handleConnected(self):
        print(self.address, 'websocket connecting')
        for client in ws_clients:
            client.send_message(self.address[0] +
                                u' - websocket connected')
        parent = self.server.parent
        if parent:
            self._id = parent.get_next_id()
            print('Connect websocket client ' + str(self._id))
            parent.add_new_player(self._CLIENT_WEBSOCKET,
                                  self, self.address[0])
        ws_clients.append(self)
        print(self.address, 'websocket connected')

    def handleClose(self):
        if self.server.parent:
            print('Disconnect websocket client ' + str(self._id))
            self.server.parent.handle_disconnect(self._id)
        ws_clients.remove(self)
        print(self.address, 'websocket closed')
        for client in ws_clients:
            client.send_message(self.address[0] +
                                u' - websocket disconnected')


class MudServer(object):
    """A basic server for text-based Multi-User Dungeon (MUD) games.

    Once created, the server will listen for players connecting using
    Telnet. Messages can then be sent to and from multiple connected
    players.

    The 'update' method should be called in a loop to keep the server
    running.
    """

    # An inner class which is instantiated for each connected client
    # to store info about them

    class _Client(object):
        """Holds information about a connected player"""

        # The type of client
        client_type = 0
        # the socket object used to communicate with this client
        socket = None
        # the ip address of this client
        address = ""
        # holds data send from the client until a full message is received
        buffer = ""
        # the last time we checked if the client was still connected
        lastcheck = 0

        def __init__(self, client_type: int,
                     socket, address: str, buffer: str,
                     lastcheck):
            self.client_type = client_type
            self.socket = socket
            self.address = address
            self.buffer = buffer
            self.lastcheck = lastcheck

    _CLIENT_TELNET = 1
    _CLIENT_WEBSOCKET = 2

    # Used to store different types of occurences
    _EVENT_NEW_PLAYER = 1
    _EVENT_PLAYER_LEFT = 2
    _EVENT_COMMAND = 3

    # Different states we can be in while reading data from client
    # See _process_sent_data function
    _READ_STATE_NORMAL = 1
    _READ_STATE_COMMAND = 2
    _READ_STATE_SUBNEG = 3

    # Command codes used by Telnet protocol
    # See _process_sent_data function
    _TN_INTERPRET_AS_COMMAND = 255
    _TN_ARE_YOU_THERE = 246
    _TN_WILL = 251
    _TN_WONT = 252
    _TN_DO = 253
    _TN_DONT = 254
    _TN_SUBNEGOTIATION_START = 250
    _TN_SUBNEGOTIATION_END = 240

    # socket used to listen for new clients
    _listen_socket = None
    # holds info on clients. Maps client id to _Client object
    _clients = {}
    # counter for assigning each client a new id
    _nextid = 0
    # list of occurences waiting to be handled by the code
    _events = []
    # list of newly-added occurences
    _new_events = []

    _WS_PORT = 6221

    def get_next_id(self) -> int:
        """Get next id
        """
        return self._nextid

    def close_sig_handler(self, signal, frame) -> None:
        """Close handler
        """
        self._websocket_server_thread.kill()
        self._websocket_server.close()
        print('Websocket server closed')
        self.shutdown()
        sys.exit()

    def run_websocket_server(self, tls: bool,
                             cert: str, key: str, ver) -> None:
        """start the websocket server
        """
        if not tls:
            self._websocket_server = \
                WebSocketServer('localhost', self._WS_PORT, MudServerWS, self)
        else:
            self._websocket_server = \
                tlsWebSocketServer('localhost', self._WS_PORT,
                                   MudServerWS, cert, key, ver)
        signal.signal(signal.SIGINT, self.close_sig_handler)
        print('Websocket server starting on port ' + str(self._WS_PORT))
        self._websocket_server_thread = \
            threadWithTrace(target=self._websocket_server.serveforever,
                            args=(), daemon=True)
        self._websocket_server_thread.start()
        print('Websocket server running')

    def __init__(self, tls=False,
                 cert='./cert.pem', key='./key.pem',
                 ver=ssl.PROTOCOL_TLS_SERVER):
        """Constructs the MudServer object and starts listening for
        new players.
        """

        self.run_websocket_server(tls, cert, key, ver)

        self._clients = {}
        self._nextid = 0
        self._events = []
        self._new_events = []

        # create a new tcp socket which will be used to listen for
        # new clients
        self._listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # set a special option on the socket which allows the port to
        # be used immediately without having to wait
        self._listen_socket.setsockopt(socket.SOL_SOCKET,
                                       socket.SO_REUSEADDR, 1)

        # bind the socket to an ip address and port. Port 23 is the standard
        # telnet port which telnet clients will use, however on some
        # platforms this requires root permissions, so we use a higher
        # arbitrary port number instead: 1234. Address 0.0.0.0 means
        # that we will bind to all of the available network interfaces
        self._listen_socket.bind(("0.0.0.0", 35123))

        # set to non-blocking mode. This means that when we call
        # 'accept', it will return immediately without waiting for a
        # connection
        self._listen_socket.setblocking(False)

        # start listening for connections on the socket
        self._listen_socket.listen(1)

    def update(self) -> None:
        """Checks for new players, disconnected players, and new
        messages sent from players. This method must be called before
        up-to-date info can be obtained from the 'get_new_players',
        'get_disconnected_players' and 'get_commands' methods.
        It should be called in a loop to keep the game running.
        """

        # check for new stuff
        self._check_for_new_connections()
        self._check_for_disconnected()
        self._check_for_messages()

        # move the new events into the main events list so that they can be
        # obtained with 'get_new_players', 'get_disconnected_players' and
        # 'get_commands'. The previous events are discarded
        self._events = list(self._new_events)
        self._new_events = []

    def get_new_players(self) -> []:
        """Returns a list containing info on any new players that have
        entered the game since the last call to 'update'. Each item in
        the list is a player id number.
        """
        retval = []
        # go through all the events in the main list
        for evnt in self._events:
            # if the event is a new player occurence, add the info to
            # the list
            if evnt[0] == self._EVENT_NEW_PLAYER:
                retval.append(evnt[1])
        # return the info list
        return retval

    def get_disconnected_players(self) -> []:
        """Returns a list containing info on any players that have left
        the game since the last call to 'update'. Each item in the list
        is a player id number.
        """
        retval = []
        # go through all the events in the main list
        for evnt in self._events:
            # if the event is a player disconnect occurence, add the info to
            # the list
            if evnt[0] == self._EVENT_PLAYER_LEFT:
                retval.append(evnt[1])
        # return the info list
        return retval

    def get_commands(self) -> []:
        """Returns a list containing any commands sent from players
        since the last call to 'update'. Each item in the list is a
        3-tuple containing the id number of the sending player, a
        string containing the command (i.e. the first word of what
        they typed), and another string containing the text after the
        command
        """
        retval = []
        # go through all the events in the main list
        for evnt in self._events:
            # if the event is a command occurence, add the info to the list
            if evnt[0] == self._EVENT_COMMAND:
                retval.append((evnt[1], evnt[2], evnt[3]))
        # return the info list
        return retval

    def player_using_web_interface(self, pid: int) -> bool:
        """Returns true if the player with the given id is
        using the web interface
        """
        try:
            clid = self._clients[pid]
        except BaseException:
            print('player_using_web_interface: client index ' +
                  str(pid) + ' was not found')
            return False
        if clid.client_type == self._CLIENT_WEBSOCKET:
            return True
        return False

    def _remove_web_socket_commands(self, pid: int, message: str) -> str:
        """Removes special commands used by the web interface
        """
        try:
            cli = self._clients[pid]
        except BaseException:
            print('_remove_web_socket_commands: client index ' +
                  str(pid) + ' was not found')
            return message
        if cli.client_type != self._CLIENT_WEBSOCKET:
            if '****TITLE****' in message:
                message = message.replace('****TITLE****', '')
            if '****CLEAR****' in message:
                message = message.replace('****CLEAR****', '')
            if '****DISCONNECT****' in message:
                message = message.replace('****DISCONNECT****', '')
        return message

    def send_message_wrap(self, to_id, prefix, message: str) -> None:
        """Sends the text in the 'message' parameter to the player with
        the id number given in the 'to' parameter. The text will be
        printed out in the player's terminal.
        """
        try:
            clid = self._clients[to_id]
        except BaseException:
            print('send_message_wrap: client index ' +
                  str(to_id) + ' was not found')
            return
        # Don't wrap on the websockets version, because html
        # will do this for us
        if clid.client_type == self._CLIENT_WEBSOCKET:
            self.send_message(to_id, message)
            return

        message = self._remove_web_socket_commands(to_id, message)

        # we make sure to put a newline on the end so the client receives
        # the message on its own line
        # print("sending...")
        # self._attempt_send(to, cmsg(message) + "\n\r")
        wrapped = textwrap.wrap(message, width=65)
        prepend_char = '<f15><b0>'
        if prefix:
            prepend_char = prefix
        for message_line in wrapped:
            send_ctr = 0
            while not self._attempt_send(to_id,
                                         cmsg(prepend_char + message_line) +
                                         '\n'):
                time.sleep(1)
                send_ctr += 1
                if send_ctr > 4:
                    break
        self._attempt_send(to_id, '\n')

    def send_message(self, to_id: int, message: str) -> None:
        """Sends the text in the 'message' parameter to the player with
        the id number given in the 'to' parameter. The text will be
        printed out in the player's terminal.
        """
        previous_timing = time.time()

        message = self._remove_web_socket_commands(to_id, message)

        previous_timing = \
            show_timing(previous_timing, "_remove_web_socket_commands")

        # we make sure to put a newline on the end so the client receives
        # the message on its own line
        # print("sending...")
        # self._attempt_send(to, cmsg(message) + "\n\r")
        send_ctr = 0
        while not self._attempt_send(to_id,
                                     cmsg('<f15><b0>' + message) +
                                     '\n'):
            time.sleep(1)
            send_ctr += 1
            if send_ctr > 4:
                break
        previous_timing = \
            show_timing(previous_timing, "_attempt_send")

    def send_image(self, to_id, message, noDelay=False) -> None:
        """Sends the ANSI image in the 'message' parameter to the player with
        the id number given in the 'to' parameter. The text will be
        printed out in the player's terminal.
        """
        if '\n' not in message:
            return
        message_lines = message.split('\n')
        if len(message_lines) < 10:
            return
        try:
            clid = self._clients[to_id]
        except BaseException:
            print('send_image: client index ' + str(to_id) +
                  ' was not found')
            return
        try:
            # look up the client in the client map and use 'sendall' to send
            # the message string on the socket. 'sendall' ensures that
            # all of the data is sent in one go
            linectr = len(message_lines)
            if clid.client_type == self._CLIENT_TELNET:
                for line_str in message_lines:
                    if linectr <= 30:
                        msg_str = line_str + '\n'
                        clid.socket.sendall(bytearray(msg_str, 'utf-8'))
                        time.sleep(0.03)
                    linectr -= 1
            elif clid.client_type == self._CLIENT_WEBSOCKET:
                clid.socket.send_message('****IMAGE****' + message)
            if clid.client_type == self._CLIENT_TELNET:
                clid.socket.sendall(bytearray(cmsg('<b0>'), 'utf-8'))
            elif clid.client_type == self._CLIENT_WEBSOCKET:
                clid.socket.send_message(cmsg('<b0>'))
        # KeyError will be raised if there is no client with the given id in
        # the map
        except KeyError as ex:
            print("Couldnt send image to Player ID " + str(to_id) +
                  ", socket error: " + str(ex))
        except BlockingIOError as ex:
            print("Couldnt send image to Player ID " + str(to_id) +
                  ", socket error: " + str(ex))
        # If there is a connection problem with the client (e.g. they have
        # disconnected) a socket error will be raised
        except socket.error as ex:
            print("Couldnt send image to Player ID " + str(to_id) +
                  ", socket error: " + str(ex))
            self.handle_disconnect(to_id)
        if not noDelay:
            if clid.client_type == self._CLIENT_TELNET:
                time.sleep(1)

    def send_game_board(self, to_id, message: str) -> None:
        """Sends the ANSI game board in the 'message' parameter to the player with
        the id number given in the 'to' parameter. The text will be
        printed out in the player's terminal.
        """
        if '\n' not in message:
            return
        message_lines = message.split('\n')
        try:
            # look up the client in the client map and use 'sendall' to send
            # the message string on the socket. 'sendall' ensures that
            # all of the data is sent in one go
            clid = self._clients[to_id]
            if clid.client_type == self._CLIENT_TELNET:
                for line_str in message_lines:
                    msg_str = line_str + '\n'
                    if clid.client_type == self._CLIENT_TELNET:
#                        clid.socket.sendall(bytearray(msg_str, 'utf-8'))
                        self.send_message(to_id, bytearray(msg_str, "utf-8"))
                    elif clid.client_type == self._CLIENT_WEBSOCKET:
                        clid.socket.send_message(msg_str)
                    time.sleep(0.03)
            elif clid.client_type == self._CLIENT_WEBSOCKET:
                if '<img class="playingcard' not in message:
                    clid.socket.send_message('****IMAGE****' + message)
                else:
                    clid.socket.send_message('****CLEAR****' + message)
            if clid.client_type == self._CLIENT_TELNET:
                clid.socket.sendall(bytearray(cmsg('<b0>'), 'utf-8'))
            elif clid.client_type == self._CLIENT_WEBSOCKET:
                clid.socket.send_message(cmsg('<b0>'))
        # KeyError will be raised if there is no client with the given
        # id in the map
        except KeyError as ex:
            print("Couldnt send game board to player ID " + str(to_id) +
                  ", socket error: " + str(ex))
        except BlockingIOError as ex:
            print("Couldnt send game board to player ID " + str(to_id) +
                  ", socket error: " + str(ex))
        # If there is a connection problem with the client (e.g. they have
        # disconnected) a socket error will be raised
        except socket.error as ex:
            print("Couldnt send game board to player ID " + str(to_id) +
                  ", socket error: " + str(ex))
            self.handle_disconnect(to_id)

    def shutdown(self) -> None:
        """Closes down the server, disconnecting all clients and
        closing the listen socket.
        """
        # for each client
        for clid in self._clients.values():
            # close the socket, disconnecting the client
            clid.socket.shutdown()
            clid.socket.close()
        # stop listening for new clients
        self._listen_socket.close()

    def _attempt_send(self, clid: int, data) -> bool:
        try:
            # look up the client in the client map and use 'sendall'
            # to send the message string on the socket. 'sendall'
            # ensures that all of the data is sent in one go
            clid = self._clients[clid]
            if clid.client_type == self._CLIENT_TELNET:
                clid.socket.sendall(bytearray(data, "latin1"))
            elif clid.client_type == self._CLIENT_WEBSOCKET:
                clid.socket.send_message(data)
            return True
        # KeyError will be raised if there is no client with the given
        # id in the map
        except KeyError:
            return False
        except BlockingIOError:
            return False
        # If there is a connection problem with the client (e.g. they have
        # disconnected) a socket error will be raised
        except socket.error as ex:
            if str(clid).isdigit():
                err_str = "Failed to send data."
                err_str += " Player ID " + str(clid)
                err_str += ": " + str(ex) + '. Disconnecting.'
                print(err_str)
                self.handle_disconnect(clid)
            return False
        return True

    def add_new_player(self, client_type: int,
                       joined_socket, address: str) -> int:
        """construct a new _Client object to hold info about the newly
        connected client. Use 'nextid' as the new client's id number
        """
        self._clients[self._nextid] = \
            MudServer._Client(client_type, joined_socket, address,
                              "", time.time())

        # add a new player occurence to the new events list with the
        # player's id number
        self._new_events.append((self._EVENT_NEW_PLAYER, self._nextid))

        # TODO

        # add 1 to 'nextid' so that the next client to connect will get a
        # unique id number
        self._nextid += 1
        return self._nextid - 1

    def _check_for_new_connections(self) -> None:
        # 'select' is used to check whether there is data waiting to be
        # read from the socket. We pass in 3 lists of sockets, the
        # first being those to check for readability. It returns 3
        # lists, the first being the sockets that are readable. The
        # last parameter is how long to wait - we pass in 0 so that
        # it returns immediately without waiting
        rlist, _, _ = select.select([self._listen_socket], [], [], 0)

        # if the socket wasn't in the readable list, there's no data
        # available, meaning no clients waiting to connect, and so we
        # can exit the method here
        if self._listen_socket not in rlist:
            return

        # 'accept' returns a new socket and address info which can be
        # used to communicate with the new client
        joined_socket, addr = self._listen_socket.accept()

        # set non-blocking mode on the new socket. This means that 'send'
        # and 'recv' will return immediately without waiting
        joined_socket.setblocking(False)

        self.add_new_player(self._CLIENT_TELNET, joined_socket, addr[0])

    def _check_for_disconnected(self) -> None:
        # go through all the clients
        for pid, clid in list(self._clients.items()):

            # if we last checked the client less than 5 seconds ago,
            # skip this client and move on to the next one
            if time.time() - clid.lastcheck < 5.0:
                continue

            # send the client an invisible character. It doesn't actually
            # matter what we send, we're really just checking that data can
            # still be written to the socket. If it can't, an error will be
            # raised and we'll know that the client has disconnected.
            # self._attempt_send(id, "\x00")
            self._attempt_send(pid, "\x00")

            # update the last check time
            clid.lastcheck = time.time()

    def receive_message(self, pid: int, message: str) -> None:
        """Receives a command from a player
        """
        # separate the message into the command (the first word)
        # and its parameters (the rest of the message)
        command, params = (message.split(" ", 1) + ["", ""])[:2]

        # add a command occurence to the new events list with
        # the player's id number, the command and its parameters
        # self._new_events.append((self._EVENT_COMMAND, id,
        # command.lower(), params))
        self._new_events.append((self._EVENT_COMMAND, pid,
                                 command, params))

    def _check_for_messages(self) -> None:
        # go through all the clients
        for pid, clid in list(self._clients.items()):
            if self._clients[pid].client_type != self._CLIENT_TELNET:
                continue
            sock = clid.socket
            # we use 'select' to test whether there is data waiting to
            # be read from the client socket. The function takes 3 lists
            # of sockets, the first being those to test for readability.
            # It returns 3 list of sockets, the first being those that
            # are actually readable.
            rlist, _, _ = select.select([sock], [], [], 0)

            # if the client socket wasn't in the readable list, there
            # is no new data from the client - we can skip it and move
            # on to the next one
            if sock not in rlist:
                continue

            data = None
            try:
                # read data from the socket, using a max length of 4096
                data = sock.recv(4096).decode("latin1")

            # if there is a problem reading from the socket (e.g. the client
            # has disconnected) a socket error will be raised
            except socket.error:
                print('Socket error receiving data. ' +
                      'Disconnecting Player ID ' + str(pid))
                self.handle_disconnect(pid)
                return

            if data is not None:
                # process the data, stripping out any special Telnet
                # commands
                message = self._process_sent_data(clid, data)

                # if there was a message in the data
                if message:
                    # remove any spaces, tabs etc from the start and end of
                    # the message
                    self.receive_message(pid, message.strip())

    def handle_disconnect(self, clid: int) -> None:
        """Disconnect
        """
        player_left = True
        if self._clients.get(clid):
            player_left = False
            try:
                # remove the client from the clients map
                del self._clients[clid]
                player_left = True
            except BaseException:
                print('Unable to remove client ' + str(clid))
                pass

        if player_left:
            # add a 'player left' occurence to the new events list, with the
            # player's id number
            self._new_events.append((self._EVENT_PLAYER_LEFT, clid))

    def _process_sent_data(self, client, data) -> str:
        # the Telnet protocol allows special command codes to be inserted
        # into messages. For our very simple server we don't need to
        # response to any of these codes, but we must at least detect
        # and skip over them so that we don't interpret them as text data.
        # More info on the Telnet protocol can be found here:
        # http://pcmicro.com/netfoss/telnet.html

        # start with no message and in the normal state
        message = None
        state = self._READ_STATE_NORMAL

        # go through the data a character at a time
        for char in data:
            # handle the character differently depending on the state
            # we're in: normal state
            if state == self._READ_STATE_NORMAL:
                # if we received the special 'interpret as command' code,
                # switch to 'command' state so that we handle the next
                # character as a command code and not as regular text data
                if ord(char) == self._TN_INTERPRET_AS_COMMAND:
                    state = self._READ_STATE_COMMAND

                # if we get a newline character, this is the end of the
                # message. Set 'message' to the contents of the buffer and
                # clear the buffer
                elif char == "\n":
                    message = client.buffer
                    client.buffer = ""

                # some telnet clients send the characters as soon as the
                # user types them. So if we get a backspace character,
                # this is where the user has deleted a character and we
                # should delete the last character from the buffer.
                elif char == "\x08":
                    client.buffer = client.buffer[:-1]

                # otherwise it's just a regular character - add it to the
                # buffer where we're building up the received message
                else:
                    client.buffer += char

            # command state
            elif state == self._READ_STATE_COMMAND:

                # the special 'start of subnegotiation' command code
                # indicates that the following characters are a list of
                # options until we're told otherwise. We switch into
                # 'subnegotiation' state to handle this
                if ord(char) == self._TN_SUBNEGOTIATION_START:
                    state = self._READ_STATE_SUBNEG

                # if the command code is one of the 'will', 'wont', 'do' or
                # 'dont' commands, the following character will be an option
                # code so we must remain in the 'command' state
                elif ord(char) in (self._TN_WILL, self._TN_WONT, self._TN_DO,
                                   self._TN_DONT):
                    state = self._READ_STATE_COMMAND

                # for all other command codes, there is no accompanying
                # data so we can return to 'normal' state.
                else:
                    state = self._READ_STATE_NORMAL

            # subnegotiation state
            elif state == self._READ_STATE_SUBNEG:

                # if we reach an 'end of subnegotiation' command, this
                # ends the list of options and we can return to 'normal'
                # state. Otherwise we must remain in this state
                if ord(char) == self._TN_SUBNEGOTIATION_END:
                    state = self._READ_STATE_NORMAL

        # return the contents of 'message' which is either a string or None
        return message
