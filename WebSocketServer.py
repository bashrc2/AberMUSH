__filename__ = "WebSocketServer.py"
__author__ = "Bob Mottram"
__credits__ = ["Dave P. https://github.com/dpallot"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@libreserver.org"
__status__ = "Production"
__module_group__ = "Web Interface"

'''
Based on https://github.com/dpallot/simple-websocket-server
'''

import hashlib
import base64
import socket
import struct
import ssl
import errno
import codecs
from collections import deque
from select import select
from http.server import BaseHTTPRequestHandler
from io import BytesIO

__all__ = ['WebSocket', 'WebSocketServer', 'tlsWebSocketServer']


def _check_unicode(val):
    return isinstance(val, str)


class HTTPRequest(BaseHTTPRequestHandler):
    def __init__(self, request_text):
        self.rfile = BytesIO(request_text)
        self.raw_requestline = self.rfile.readline()
        self.error_code = self.error_message = None
        self.parse_request()


_VALID_STATUS_CODES = [
    1000, 1001, 1002, 1003, 1007, 1008,
    1009, 1010, 1011, 3000, 3999, 4000, 4999
]

HANDSHAKE_STR = (
    "HTTP/1.1 101 Switching Protocols\r\n"
    "Upgrade: WebSocket\r\n"
    "Connection: Upgrade\r\n"
    "Sec-WebSocket-Accept: %(acceptstr)s\r\n\r\n"
)

FAILED_HANDSHAKE_STR = (
    "HTTP/1.1 426 Upgrade Required\r\n"
    "Upgrade: WebSocket\r\n"
    "Connection: Upgrade\r\n"
    "Sec-WebSocket-Version: 13\r\n"
    "Content-Type: text/plain\r\n\r\n"
    "This service requires use of the WebSocket protocol\r\n"
)

GUID_STR = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'

STREAM = 0x0
TEXT = 0x1
BINARY = 0x2
CLOSE = 0x8
PING = 0x9
PONG = 0xA

HEADERB1 = 1
HEADERB2 = 3
LENGTHSHORT = 4
LENGTHLONG = 5
MASK = 6
PAYLOAD = 7

MAXHEADER = 65536
MAXPAYLOAD = 33554432


class WebSocket(object):
    def __init__(self, server, sock, address):
        self.server = server
        self.client = sock
        self.address = address

        self.handshaked = False
        self.headerbuffer = bytearray()
        self.headertoread = 2048

        self.fin = 0
        self.data = bytearray()
        self.opcode = 0
        self.hasmask = 0
        self.maskarray = None
        self.length = 0
        self.lengtharray = None
        self.index = 0
        self.request = None
        self.usingtls = False

        self.frag_start = False
        self.frag_type = BINARY
        self.frag_buffer = None
        self.frag_decoder = \
            codecs.getincrementaldecoder('utf-8')(errors='strict')
        self.closed = False
        self.sendq = deque()

        self.state = HEADERB1

        # restrict the size of header and payload for security reasons
        self.maxheader = MAXHEADER
        self.maxpayload = MAXPAYLOAD

    def handleMessage(self):
        """
          Called when websocket frame is received.
          To access the frame data call self.data.

          If the frame is Text then self.data is a unicode object.
          If the frame is Binary then self.data is a bytearray object.
        """
        pass

    def handleConnected(self):
        """Called when a websocket client connects to the server.
        """
        pass

    def handleClose(self):
        """Called when a websocket server gets a Close frame from a client.
        """
        pass

    def _handlePacket(self):
        if self.opcode == CLOSE:
            pass
        elif self.opcode == STREAM:
            pass
        elif self.opcode == TEXT:
            pass
        elif self.opcode == BINARY:
            pass
        elif self.opcode in (PING, PONG):
            if len(self.data) > 125:
                raise Exception('control frame length can not be > 125')
        else:
            # unknown or reserved opcode so just close
            raise Exception('unknown opcode')

        if self.opcode == CLOSE:
            status = 1000
            reason = ''
            length = len(self.data)

            if length == 0:
                pass
            elif length >= 2:
                status = struct.unpack_from('!H', self.data[:2])[0]
                reason = self.data[2:]

                if status not in _VALID_STATUS_CODES:
                    status = 1002

                if len(reason) > 0:
                    try:
                        reason = reason.decode('utf8', errors='strict')
                    except BaseException:
                        status = 1002
            else:
                status = 1002

            self.close(status, reason)
            return

        if self.fin == 0:
            if self.opcode != STREAM:
                if self.opcode in (PING, PONG):
                    raise Exception('control messages can not be fragmented')

                self.frag_type = self.opcode
                self.frag_start = True
                self.frag_decoder.reset()

                if self.frag_type == TEXT:
                    self.frag_buffer = []
                    utf_str = self.frag_decoder.decode(self.data, final=False)
                    if utf_str:
                        self.frag_buffer.append(utf_str)
                else:
                    self.frag_buffer = bytearray()
                    self.frag_buffer.extend(self.data)

            else:
                if self.frag_start is False:
                    raise Exception('fragmentation protocol error')

                if self.frag_type == TEXT:
                    utf_str = self.frag_decoder.decode(self.data, final=False)
                    if utf_str:
                        self.frag_buffer.append(utf_str)
                else:
                    self.frag_buffer.extend(self.data)

        else:
            if self.opcode == STREAM:
                if self.frag_start is False:
                    raise Exception('fragmentation protocol error')

                if self.frag_type == TEXT:
                    utf_str = self.frag_decoder.decode(self.data, final=True)
                    self.frag_buffer.append(utf_str)
                    self.data = ''.join(self.frag_buffer)
                else:
                    self.frag_buffer.extend(self.data)
                    self.data = self.frag_buffer

                self.handleMessage()

                self.frag_decoder.reset()
                self.frag_type = BINARY
                self.frag_start = False
                self.frag_buffer = None

            elif self.opcode == PING:
                self._send_message(False, PONG, self.data)

            elif self.opcode == PONG:
                pass

            else:
                if self.frag_start is True:
                    raise Exception('fragmentation protocol error')

                if self.opcode == TEXT:
                    try:
                        self.data = self.data.decode('utf8', errors='strict')
                    except Exception as exp:
                        raise Exception('invalid utf-8 payload ' + str(exp))

                self.handleMessage()

    def _handleData(self):
        # do the HTTP header and handshake
        if self.handshaked is False:

            data = self.client.recv(self.headertoread)
            if not data:
                raise Exception('remote socket closed')

            # accumulate
            self.headerbuffer.extend(data)

            if len(self.headerbuffer) >= self.maxheader:
                raise Exception('header exceeded allowable size')

            # indicates end of HTTP header
            if b'\r\n\r\n' in self.headerbuffer:
                self.request = HTTPRequest(self.headerbuffer)

                # handshake rfc 6455
                try:
                    key = self.request.headers['Sec-WebSocket-Key']
                    k = key.encode('ascii') + GUID_STR.encode('ascii')
                    k_s_digest = hashlib.sha1(k).digest()
                    k_s = \
                        base64.b64encode(k_s_digest).decode('ascii')
                    hstr = HANDSHAKE_STR % {'acceptstr': k_s}
                    self.sendq.append((BINARY, hstr.encode('ascii')))
                    self.handshaked = True
                    self.handleConnected()
                except Exception as ex:
                    hstr = FAILED_HANDSHAKE_STR
                    self._sendBuffer(hstr.encode('ascii'), True)
                    self.client.close()
                    raise Exception('handshake failed: %s', str(ex))

        # else do normal data
        else:
            data = self.client.recv(16384)
            if not data:
                raise Exception("remote socket closed")

            for dat in data:
                self._parseMessage(dat)

    def close(self, status: int = 1000, reason: str = ''):
        """
          Send Close frame to the client. The underlying socket is only closed
          when the client acknowledges the Close frame.

          status is the closing identifier.
          reason is the reason for the close.
        """
        try:
            if self.closed is False:
                close_msg = bytearray()
                close_msg.extend(struct.pack("!H", status))
                if _check_unicode(reason):
                    close_msg.extend(reason.encode('utf-8'))
                else:
                    close_msg.extend(reason)

                self._send_message(False, CLOSE, close_msg)

        finally:
            self.closed = True

    def _sendBuffer(self, buff, send_all: bool = False):
        size = len(buff)
        tosend = size
        already_sent = 0

        while tosend > 0:
            try:
                # i should be able to send a bytearray
                sent = self.client.send(buff[already_sent:])
                if sent == 0:
                    raise RuntimeError('socket connection broken')

                already_sent += sent
                tosend -= sent

            except socket.error as ex:
                # if we have full buffers then wait for them to
                # drain and try again
                if ex.errno in [errno.EAGAIN, errno.EWOULDBLOCK]:
                    if send_all:
                        continue
                    return buff[already_sent:]
                raise ex

        return None

    def sendFragmentStart(self, data):
        """
          Send the start of a data fragment stream to a websocket client.
          Subsequent data should be sent using sendFragment().
          A fragment stream is completed when sendFragmentEnd() is called.

          If data is a unicode object then the frame is sent as Text.
          If the data is a bytearray object then the frame is sent as Binary.
        """
        opcode = BINARY
        if _check_unicode(data):
            opcode = TEXT
        self._send_message(True, opcode, data)

    def sendFragment(self, data):
        """
          see sendFragmentStart()

          If data is a unicode object then the frame is sent as Text.
          If the data is a bytearray object then the frame is sent as Binary.
        """
        self._send_message(True, STREAM, data)

    def sendFragmentEnd(self, data):
        """
          see sendFragmentEnd()

          If data is a unicode object then the frame is sent as Text.
          If the data is a bytearray object then the frame is sent as Binary.
        """
        self._send_message(False, STREAM, data)

    def send_message(self, data):
        """
          Send websocket data frame to the client.

          If data is a unicode object then the frame is sent as Text.
          If the data is a bytearray object then the frame is sent as Binary.
        """
        opcode = BINARY
        if _check_unicode(data):
            opcode = TEXT
        self._send_message(False, opcode, data)

    def _send_message(self, fin, opcode, data):

        payload = bytearray()

        bb1 = 0
        bb2 = 0
        if fin is False:
            bb1 |= 0x80
        bb1 |= opcode

        if _check_unicode(data):
            data = data.encode('utf-8')

        length = len(data)
        payload.append(bb1)

        if length <= 125:
            bb2 |= length
            payload.append(bb2)

        elif length in range(126, 65536):
            bb2 |= 126
            payload.append(bb2)
            payload.extend(struct.pack("!H", length))

        else:
            bb2 |= 127
            payload.append(bb2)
            payload.extend(struct.pack("!Q", length))

        if length > 0:
            payload.extend(data)

        self.sendq.append((opcode, payload))

    def _parseMessage(self, byte):
        # read in the header
        if self.state == HEADERB1:

            self.fin = byte & 0x80
            self.opcode = byte & 0x0F
            self.state = HEADERB2

            self.index = 0
            self.length = 0
            self.lengtharray = bytearray()
            self.data = bytearray()

            rsv = byte & 0x70
            if rsv != 0:
                raise Exception('RSV bit must be 0')

        elif self.state == HEADERB2:
            mask = byte & 0x80
            length = byte & 0x7F

            if self.opcode == PING and length > 125:
                raise Exception('ping packet is too large')

            if mask == 128:
                self.hasmask = True
            else:
                self.hasmask = False

            if length <= 125:
                self.length = length

                # if we have a mask we must read it
                if self.hasmask is True:
                    self.maskarray = bytearray()
                    self.state = MASK
                else:
                    # if there is no mask and no payload we are done
                    if self.length <= 0:
                        try:
                            self._handlePacket()
                        finally:
                            self.state = HEADERB1
                            self.data = bytearray()

                    # we have no mask and some payload
                    else:
                        # self.index = 0
                        self.data = bytearray()
                        self.state = PAYLOAD

            elif length == 126:
                self.lengtharray = bytearray()
                self.state = LENGTHSHORT

            elif length == 127:
                self.lengtharray = bytearray()
                self.state = LENGTHLONG

        elif self.state == LENGTHSHORT:
            self.lengtharray.append(byte)

            if len(self.lengtharray) > 2:
                raise Exception('short length exceeded allowable size')

            if len(self.lengtharray) == 2:
                self.length = struct.unpack_from('!H', self.lengtharray)[0]

                if self.hasmask is True:
                    self.maskarray = bytearray()
                    self.state = MASK
                else:
                    # if there is no mask and no payload we are done
                    if self.length <= 0:
                        try:
                            self._handlePacket()
                        finally:
                            self.state = HEADERB1
                            self.data = bytearray()

                    # we have no mask and some payload
                    else:
                        # self.index = 0
                        self.data = bytearray()
                        self.state = PAYLOAD

        elif self.state == LENGTHLONG:

            self.lengtharray.append(byte)

            if len(self.lengtharray) > 8:
                raise Exception('long length exceeded allowable size')

            if len(self.lengtharray) == 8:
                self.length = struct.unpack_from('!Q', self.lengtharray)[0]

                if self.hasmask is True:
                    self.maskarray = bytearray()
                    self.state = MASK
                else:
                    # if there is no mask and no payload we are done
                    if self.length <= 0:
                        try:
                            self._handlePacket()
                        finally:
                            self.state = HEADERB1
                            self.data = bytearray()

                    # we have no mask and some payload
                    else:
                        # self.index = 0
                        self.data = bytearray()
                        self.state = PAYLOAD

        # MASK STATE
        elif self.state == MASK:
            self.maskarray.append(byte)

            if len(self.maskarray) > 4:
                raise Exception('mask exceeded allowable size')

            if len(self.maskarray) == 4:
                # if there is no mask and no payload we are done
                if self.length <= 0:
                    try:
                        self._handlePacket()
                    finally:
                        self.state = HEADERB1
                        self.data = bytearray()

                # we have no mask and some payload
                else:
                    # self.index = 0
                    self.data = bytearray()
                    self.state = PAYLOAD

        # PAYLOAD STATE
        elif self.state == PAYLOAD:
            if self.hasmask is True:
                self.data.append(byte ^ self.maskarray[self.index % 4])
            else:
                self.data.append(byte)

            # if length exceeds allowable size then we except and remove
            # the connection
            if len(self.data) >= self.maxpayload:
                raise Exception('payload exceeded allowable size')

            # check if we have processed length bytes; if so we are done
            if (self.index+1) == self.length:
                try:
                    self._handlePacket()
                finally:
                    # self.index = 0
                    self.state = HEADERB1
                    self.data = bytearray()
            else:
                self.index += 1


class WebSocketServer(object):
    def __init__(self, host, port, websocketclass, parent,
                 select_interval: float = 0.1):
        self.websocketclass = websocketclass
        self.parent = parent

        if host == '':
            host = None

        if host is None:
            fam = socket.AF_INET6
        else:
            fam = 0

        host_info = \
            socket.getaddrinfo(host, port, fam, socket.SOCK_STREAM,
                               socket.IPPROTO_TCP, socket.AI_PASSIVE)
        self.serversocket = socket.socket(host_info[0][0], host_info[0][1],
                                          host_info[0][2])
        self.serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serversocket.bind(host_info[0][4])
        self.serversocket.listen(5)
        self.select_interval = select_interval
        self.connections = {}
        self.listeners = [self.serversocket]

    def _decorateSocket(self, sock):
        return sock

    def _constructWebSocket(self, sock, address):
        return self.websocketclass(self, sock, address)

    def close(self):
        self.serversocket.close()

        for _, conn in self.connections.items():
            conn.close()
            self._handleClose(conn)

    def _handleClose(self, client):
        client.client.close()
        # only call handleClose when we have a successful websocket connection
        if client.handshaked:
            try:
                client.handleClose()
            except BaseException:
                pass

    def serveonce(self):
        writers = []
        for fileno in self.listeners:
            if fileno == self.serversocket:
                continue
            client = self.connections[fileno]
            if client.sendq:
                writers.append(fileno)

        rlist, wlist, xlist = \
            select(self.listeners, writers, self.listeners,
                   self.select_interval)

        for ready in wlist:
            client = self.connections[ready]
            try:
                while client.sendq:
                    opcode, payload = client.sendq.popleft()
                    remaining = client._sendBuffer(payload)
                    if remaining is not None:
                        client.sendq.appendleft((opcode, remaining))
                        break
                    if opcode == CLOSE:
                        raise Exception('received client close')

            except BaseException:
                self._handleClose(client)
                del self.connections[ready]
                self.listeners.remove(ready)

        for ready in rlist:
            if ready == self.serversocket:
                sock = None
                try:
                    sock, address = self.serversocket.accept()
                    newsock = self._decorateSocket(sock)
                    newsock.setblocking(0)
                    fileno = newsock.fileno()
                    self.connections[fileno] = \
                        self._constructWebSocket(newsock, address)
                    self.listeners.append(fileno)
                except BaseException:
                    if sock is not None:
                        sock.close()
            else:
                if ready not in self.connections:
                    continue
                client = self.connections[ready]
                try:
                    client._handleData()
                except BaseException:
                    self._handleClose(client)
                    del self.connections[ready]
                    self.listeners.remove(ready)

        for failed in xlist:
            if failed == self.serversocket:
                self.close()
                raise Exception('server socket failed')
            if failed not in self.connections:
                continue
            client = self.connections[failed]
            self._handleClose(client)
            del self.connections[failed]
            self.listeners.remove(failed)

    def serveforever(self):
        while True:
            self.serveonce()


class tlsWebSocketServer(WebSocketServer):

    def __init__(self, host: str, port: int,
                 websocketclass, certfile=None,
                 keyfile=None, version=ssl.PROTOCOL_TLS_SERVER,
                 select_interval: float = 0.1, tls_context=None):

        WebSocketServer.__init__(self, host, port,
                                 websocketclass, select_interval)

        if tls_context is None:
            self.context = ssl.SSLContext(version)
            # if you get a permission error here:
            #     usermod -g ssl-cert abermush
            # and ensure that the group is set to ssl-cert in the daemon
            self.context.load_cert_chain(certfile, keyfile)
        else:
            self.context = tls_context

    def close(self):
        super(tlsWebSocketServer, self).close()

    def _decorateSocket(self, sock):
        sslsock = self.context.wrap_socket(sock, server_side=True)
        return sslsock

    def _constructWebSocket(self, sock, address):
        ws = self.websocketclass(self, sock, address)
        ws.usingtls = True
        return ws

    def serveforever(self):
        super(tlsWebSocketServer, self).serveforever()
