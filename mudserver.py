__filename__ = "mudserver.py"
__author__ = "Bob Mottram"
__credits__ = ["Bartek Radwanski", "Mark Frimston",
               "Dave P. https://github.com/dpallot"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@freedombone.net"
__status__ = "Production"

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
import textwrap
from cmsg import cmsg
from WebSocketServer import WebSocket, WebSocketServer
from threads import threadWithTrace

ws_clients = []


class MudServerWS(WebSocket):
    _id = -1

    _CLIENT_WEBSOCKET = 2

    def handleMessage(self):
        # web interface sent a message
        # print('Player ' + str(self._id) + u' sent: ' + self.data)
        if self._id < 0:
            return
        self.server.parent.receiveMessage(self._id, self.data.strip())

    def handleConnected(self):
        print(self.address, 'websocket connecting')
        for client in ws_clients:
            client.sendMessage(self.address[0] +
                               u' - websocket connected')
        if self.server.parent:
            self._id = self.server.parent.getNextId()
            print('Connect websocket client ' + str(self._id))
            self.server.parent.add_new_player(self._CLIENT_WEBSOCKET, self,
                                              self.address[0])
        ws_clients.append(self)
        print(self.address, 'websocket connected')

    def handleClose(self):
        if self.server.parent:
            print('Disconnect websocket client ' + str(self._id))
            self.server.parent.handleDisconnect(self._id)
        ws_clients.remove(self)
        print(self.address, 'websocket closed')
        for client in ws_clients:
            client.sendMessage(self.address[0] +
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

    def getNextId(self) -> int:
        return self._nextid

    def close_sig_handler(self, signal, frame):
        self._websocket_server_thread.kill()
        self._websocket_server.close()
        print('Websocket server closed')
        self.shutdown()
        sys.exit()

    def run_websocket_server(self):
        """start the websocket server
        """
        self._websocket_server = \
            WebSocketServer('localhost', self._WS_PORT, MudServerWS, self)
        signal.signal(signal.SIGINT, self.close_sig_handler)
        print('Websocket server starting on port ' + str(self._WS_PORT))
        self._websocket_server_thread = \
            threadWithTrace(target=self._websocket_server.serveforever,
                            args=(), daemon=True)
        self._websocket_server_thread.start()
        print('Websocket server running')

    def __init__(self):
        """Constructs the MudServer object and starts listening for
        new players.
        """

        self.run_websocket_server()

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

    def update(self):
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

    def get_new_players(self):
        """Returns a list containing info on any new players that have
        entered the game since the last call to 'update'. Each item in
        the list is a player id number.
        """
        retval = []
        # go through all the events in the main list
        for ev in self._events:
            # if the event is a new player occurence, add the info to
            # the list
            if ev[0] == self._EVENT_NEW_PLAYER:
                retval.append(ev[1])
        # return the info list
        return retval

    def get_disconnected_players(self):
        """Returns a list containing info on any players that have left
        the game since the last call to 'update'. Each item in the list
        is a player id number.
        """
        retval = []
        # go through all the events in the main list
        for ev in self._events:
            # if the event is a player disconnect occurence, add the info to
            # the list
            if ev[0] == self._EVENT_PLAYER_LEFT:
                retval.append(ev[1])
        # return the info list
        return retval

    def get_commands(self):
        """Returns a list containing any commands sent from players
        since the last call to 'update'. Each item in the list is a
        3-tuple containing the id number of the sending player, a
        string containing the command (i.e. the first word of what
        they typed), and another string containing the text after the
        command
        """
        retval = []
        # go through all the events in the main list
        for ev in self._events:
            # if the event is a command occurence, add the info to the list
            if ev[0] == self._EVENT_COMMAND:
                retval.append((ev[1], ev[2], ev[3]))
        # return the info list
        return retval

    def playerUsingWebInterface(self, id: int) -> bool:
        """Returns true if the player with the given id is
        using the web interface
        """
        cl = self._clients[id]
        if cl.client_type == self._CLIENT_WEBSOCKET:
            return True
        return False

    def removeWebSocketCommands(self, id: int, message: str) -> str:
        """Removes special commands used by the web interface
        """
        cl = self._clients[id]
        if cl.client_type != self._CLIENT_WEBSOCKET:
            if '****TITLE****' in message:
                message = message.replace('****TITLE****', '')
            if '****CLEAR****' in message:
                message = message.replace('****CLEAR****', '')
            if '****DISCONNECT****' in message:
                message = message.replace('****DISCONNECT****', '')
        return message

    def sendMessageWrap(self, to, prefix, message: str):
        """Sends the text in the 'message' parameter to the player with
        the id number given in the 'to' parameter. The text will be
        printed out in the player's terminal.
        """
        cl = self._clients[to]
        # Don't wrap on the websockets version, because html
        # will do this for us
        if cl.client_type == self._CLIENT_WEBSOCKET:
            self.sendMessage(to, message)
            return

        message = self.removeWebSocketCommands(to, message)

        # we make sure to put a newline on the end so the client receives
        # the message on its own line
        # print("sending...")
        # self._attempt_send(to, cmsg(message)+"\n\r")
        wrapped = textwrap.wrap(message, width=65)
        prependChar = '<f15><b0>'
        if prefix:
            prependChar = prefix
        for messageLine in wrapped:
            sendCtr = 0
            while not self._attempt_send(to,
                                         cmsg(prependChar + messageLine) +
                                         '\n'):
                time.sleep(1)
                sendCtr += 1
                if sendCtr > 4:
                    break
        self._attempt_send(to, '\n')

    def sendMessage(self, to: int, message: str):
        """Sends the text in the 'message' parameter to the player with
        the id number given in the 'to' parameter. The text will be
        printed out in the player's terminal.
        """
        message = self.removeWebSocketCommands(to, message)
        # we make sure to put a newline on the end so the client receives
        # the message on its own line
        # print("sending...")
        # self._attempt_send(to, cmsg(message)+"\n\r")
        sendCtr = 0
        while not self._attempt_send(to,
                                     cmsg('<f15><b0>' + message) +
                                     '\n'):
            time.sleep(1)
            sendCtr += 1
            if sendCtr > 4:
                break

    def sendImage(self, to, message, noDelay=False) -> None:
        """Sends the ANSI image in the 'message' parameter to the player with
        the id number given in the 'to' parameter. The text will be
        printed out in the player's terminal.
        """
        if '\n' not in message:
            return
        messageLines = message.split('\n')
        if len(messageLines) < 10:
            return
        cl = self._clients[to]
        try:
            # look up the client in the client map and use 'sendall' to send
            # the message string on the socket. 'sendall' ensures that
            # all of the data is sent in one go
            linectr = len(messageLines)
            if cl.client_type == self._CLIENT_TELNET:
                for lineStr in messageLines:
                    if linectr <= 30:
                        msgStr = lineStr + '\n'
                        cl.socket.sendall(bytearray(msgStr, 'utf-8'))
                        time.sleep(0.03)
                    linectr -= 1
            elif cl.client_type == self._CLIENT_WEBSOCKET:
                cl.socket.sendMessage('****IMAGE****' + message)
            if cl.client_type == self._CLIENT_TELNET:
                cl.socket.sendall(bytearray(cmsg('<b0>'), 'utf-8'))
            elif cl.client_type == self._CLIENT_WEBSOCKET:
                cl.socket.sendMessage(cmsg('<b0>'))
        # KeyError will be raised if there is no client with the given id in
        # the map
        except KeyError as e:
            print("Couldnt send image to Player ID " + str(to) +
                  ", socket error: " + str(e))
            pass
        except BlockingIOError as e:
            print("Couldnt send image to Player ID " + str(to) +
                  ", socket error: " + str(e))
            pass
        # If there is a connection problem with the client (e.g. they have
        # disconnected) a socket error will be raised
        except socket.error as e:
            print("Couldnt send image to Player ID " + str(to) +
                  ", socket error: " + str(e))
            self.handleDisconnect(to)
        if not noDelay:
            if cl.client_type == self._CLIENT_TELNET:
                time.sleep(1)

    def send_game_board(self, to, message) -> None:
        """Sends the ANSI game board in the 'message' parameter to the player with
        the id number given in the 'to' parameter. The text will be
        printed out in the player's terminal.
        """
        if '\n' not in message:
            return
        messageLines = message.split('\n')
        try:
            # look up the client in the client map and use 'sendall' to send
            # the message string on the socket. 'sendall' ensures that
            # all of the data is sent in one go
            cl = self._clients[to]
            if cl.client_type == self._CLIENT_TELNET:
                for lineStr in messageLines:
                    msgStr = lineStr + '\n'
                    if cl.client_type == self._CLIENT_TELNET:
                        cl.socket.sendall(bytearray(msgStr, 'utf-8'))
                    elif cl.client_type == self._CLIENT_WEBSOCKET:
                        cl.socket.sendMessage(msgStr)
                    time.sleep(0.03)
            elif cl.client_type == self._CLIENT_WEBSOCKET:
                if '<img class="playingcard' not in message:
                    cl.socket.sendMessage('****IMAGE****' + message)
                else:
                    cl.socket.sendMessage('****CLEAR****' + message)
            if cl.client_type == self._CLIENT_TELNET:
                cl.socket.sendall(bytearray(cmsg('<b0>'), 'utf-8'))
            elif cl.client_type == self._CLIENT_WEBSOCKET:
                cl.socket.sendMessage(cmsg('<b0>'))
        # KeyError will be raised if there is no client with the given
        # id in the map
        except KeyError as e:
            print("Couldnt send game board to player ID " + str(to) +
                  ", socket error: " + str(e))
            pass
        except BlockingIOError as e:
            print("Couldnt send game board to player ID " + str(to) +
                  ", socket error: " + str(e))
            pass
        # If there is a connection problem with the client (e.g. they have
        # disconnected) a socket error will be raised
        except socket.error as e:
            print("Couldnt send game board to player ID " + str(to) +
                  ", socket error: " + str(e))
            self.handleDisconnect(to)

    def shutdown(self):
        """Closes down the server, disconnecting all clients and
        closing the listen socket.
        """
        # for each client
        for cl in self._clients.values():
            # close the socket, disconnecting the client
            cl.socket.shutdown()
            cl.socket.close()
        # stop listening for new clients
        self._listen_socket.close()

    def _attempt_send(self, clid: int, data) -> bool:
        try:
            # look up the client in the client map and use 'sendall'
            # to send the message string on the socket. 'sendall'
            # ensures that all of the data is sent in one go
            cl = self._clients[clid]
            if cl.client_type == self._CLIENT_TELNET:
                cl.socket.sendall(bytearray(data, "latin1"))
            elif cl.client_type == self._CLIENT_WEBSOCKET:
                cl.socket.sendMessage(data)
            return True
        # KeyError will be raised if there is no client with the given
        # id in the map
        except KeyError as e:
            print("Failed to send data. Player ID " + str(clid) +
                  ": " + str(e))
            pass
            return False
        except BlockingIOError as e:
            print("Failed to send data. Player ID " + str(clid) +
                  ": " + str(e))
            pass
            return False
        # If there is a connection problem with the client (e.g. they have
        # disconnected) a socket error will be raised
        except socket.error as e:
            print("Failed to send data. Player ID " + str(clid) +
                  ": " + str(e) + '. Disconnecting.')
            self.handleDisconnect(clid)
            return False
        return True

    def add_new_player(self, client_type: int,
                       joined_socket, address: str):
        # construct a new _Client object to hold info about the newly
        # connected client. Use 'nextid' as the new client's id number
        self._clients[self._nextid] = \
            MudServer._Client(client_type, joined_socket, address,
                              "", time.time())

        # add a new player occurence to the new events list with the
        # player's id number
        self._new_events.append((self._EVENT_NEW_PLAYER, self._nextid))

        # add 1 to 'nextid' so that the next client to connect will get a
        # unique id number
        self._nextid += 1
        return self._nextid - 1

    def _check_for_new_connections(self):
        # 'select' is used to check whether there is data waiting to be
        # read from the socket. We pass in 3 lists of sockets, the
        # first being those to check for readability. It returns 3
        # lists, the first being the sockets that are readable. The
        # last parameter is how long to wait - we pass in 0 so that
        # it returns immediately without waiting
        rlist, wlist, xlist = select.select([self._listen_socket], [], [], 0)

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

    def _check_for_disconnected(self):
        # go through all the clients
        for id, cl in list(self._clients.items()):

            # if we last checked the client less than 5 seconds ago,
            # skip this client and move on to the next one
            if time.time() - cl.lastcheck < 5.0:
                continue

            # send the client an invisible character. It doesn't actually
            # matter what we send, we're really just checking that data can
            # still be written to the socket. If it can't, an error will be
            # raised and we'll know that the client has disconnected.
            # self._attempt_send(id, "\x00")
            self._attempt_send(id, "\x00")

            # update the last check time
            cl.lastcheck = time.time()

    def receiveMessage(self, id: int, message: str):
        """Receives a command from a player
        """
        # separate the message into the command (the first word)
        # and its parameters (the rest of the message)
        command, params = (message.split(" ", 1) + ["", ""])[:2]

        # add a command occurence to the new events list with
        # the player's id number, the command and its parameters
        # self._new_events.append((self._EVENT_COMMAND, id,
        # command.lower(), params))
        self._new_events.append((self._EVENT_COMMAND, id,
                                 command, params))

    def _check_for_messages(self):
        # go through all the clients
        for id, cl in list(self._clients.items()):
            if self._clients[id].client_type != self._CLIENT_TELNET:
                continue
            sock = cl.socket
            # we use 'select' to test whether there is data waiting to
            # be read from the client socket. The function takes 3 lists
            # of sockets, the first being those to test for readability.
            # It returns 3 list of sockets, the first being those that
            # are actually readable.
            rlist, wlist, xlist = select.select([sock], [], [], 0)

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
                      'Disconnecting Player ID ' + str(id))
                self.handleDisconnect(id)
                return

            if data is not None:
                # process the data, stripping out any special Telnet
                # commands
                message = self._process_sent_data(cl, data)

                # if there was a message in the data
                if message:
                    # remove any spaces, tabs etc from the start and end of
                    # the message
                    self.receiveMessage(id, message.strip())

    def handleDisconnect(self, clid: int):
        playerLeft = False
        try:
            # remove the client from the clients map
            del(self._clients[clid])
            playerLeft = True
        except BaseException:
            print('Unable to remove client ' + str(clid))

        if playerLeft:
            # add a 'player left' occurence to the new events list, with the
            # player's id number
            self._new_events.append((self._EVENT_PLAYER_LEFT, clid))

    def _process_sent_data(self, client, data):
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
        for c in data:
            # handle the character differently depending on the state
            # we're in: normal state
            if state == self._READ_STATE_NORMAL:
                # if we received the special 'interpret as command' code,
                # switch to 'command' state so that we handle the next
                # character as a command code and not as regular text data
                if ord(c) == self._TN_INTERPRET_AS_COMMAND:
                    state = self._READ_STATE_COMMAND

                # if we get a newline character, this is the end of the
                # message. Set 'message' to the contents of the buffer and
                # clear the buffer
                elif c == "\n":
                    message = client.buffer
                    client.buffer = ""

                # some telnet clients send the characters as soon as the
                # user types them. So if we get a backspace character,
                # this is where the user has deleted a character and we
                # should delete the last character from the buffer.
                elif c == "\x08":
                    client.buffer = client.buffer[:-1]

                # otherwise it's just a regular character - add it to the
                # buffer where we're building up the received message
                else:
                    client.buffer += c

            # command state
            elif state == self._READ_STATE_COMMAND:

                # the special 'start of subnegotiation' command code
                # indicates that the following characters are a list of
                # options until we're told otherwise. We switch into
                # 'subnegotiation' state to handle this
                if ord(c) == self._TN_SUBNEGOTIATION_START:
                    state = self._READ_STATE_SUBNEG

                # if the command code is one of the 'will', 'wont', 'do' or
                # 'dont' commands, the following character will be an option
                # code so we must remain in the 'command' state
                elif ord(c) in (self._TN_WILL, self._TN_WONT, self._TN_DO,
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
                if ord(c) == self._TN_SUBNEGOTIATION_END:
                    state = self._READ_STATE_NORMAL

        # return the contents of 'message' which is either a string or None
        return message
