__filename__ = "mudserverws.py"
__author__ = "Bob Mottram"
__credits__ = ["Dave P. https://github.com/dpallot"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@freedombone.net"
__status__ = "Production"

'''
   import signal
   import sys
   from WebSocketServer import WebSocket, WebSocketServer
   from  mudserverws import MudServerWS

   server = WebSocketServer('localhost', port, MudServerWS)

   def close_sig_handler(signal, frame):
      server.close()
      sys.exit()

   signal.signal(signal.SIGINT, close_sig_handler)

   server.serveforever()
'''

from WebSocketServer import WebSocket

clients = []


class MudServerWS(WebSocket):
    def handleMessage(self):
        for client in clients:
            if client != self:
                client.sendMessage(self.address[0] + u' - ' + self.data)

    def handleConnected(self):
        print(self.address, 'connected')
        for client in clients:
            client.sendMessage(self.address[0] + u' - connected')
        clients.append(self)

    def handleClose(self):
        clients.remove(self)
        print(self.address, 'closed')
        for client in clients:
            client.sendMessage(self.address[0] + u' - disconnected')
