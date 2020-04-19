__filename__ = "webserver.py"
__author__ = "Bob Mottram"
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@freedombone.net"
__status__ = "Production"

import os
import time
import requests
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from functools import partial
from hashlib import sha1


def noOfAccounts(baseDir: str) -> bool:
    """Returns the number of player accounts on the system
    """
    accountCtr = 0
    for subdir, dirs, files in os.walk(baseDir + '/players'):
        for account in files:
            if account != 'Guest.player' and \
               not account.endswith('.template'):
                accountCtr += 1
    return accountCtr


def htmlHeader(cssFilename: str, css=None, refreshSec=0, lang='en') -> str:
    if refreshSec == 0:
        meta = '  <meta charset="utf-8">\n'
    else:
        meta = \
            '  <meta http-equiv="Refresh" content="' + \
            str(refreshSec) + '" charset="utf-8">\n'

    if not css:
        if '/' in cssFilename:
            cssFilename = cssFilename.split('/')[-1]
        htmlStr = '<!DOCTYPE html>\n'
        htmlStr += '<html lang="' + lang + '">\n'
        htmlStr += meta
        htmlStr += '  <style>\n'
        htmlStr += '    @import url("' + cssFilename + '");\n'
        htmlStr += '    background-color: #282c37'
        htmlStr += '  </style>\n'
        htmlStr += '  <body>\n'
    else:
        htmlStr = '<!DOCTYPE html>\n'
        htmlStr += '<html lang="' + lang + '">\n'
        htmlStr += meta
        htmlStr += '  <style>\n' + css + '</style>\n'
        htmlStr += '  <body>\n'
    return htmlStr


def htmlFooter() -> str:
    htmlStr = '  </body>\n'
    htmlStr += '</html>\n'
    return htmlStr


def htmlLogin(baseDir: str, registrationsOpen: bool,
              registrationsRemaining: int,
              autocomplete=True) -> str:
    """Shows the login screen
    """
    loginImageFilename = baseDir + '/webserver/login.png'

    accounts = noOfAccounts(baseDir)
    if accounts > 0:
        loginText = \
            '<p class="login-text">' + \
            'Welcome. Please enter your login details below.' + \
            '</p>'
    else:
        loginText = \
            '<p class="login-text">' + \
            'Please enter some credentials' + '</p>'
        loginText += \
            '<p class="login-text">' + \
            'You will become the admin of this site.' + \
            '</p>'

    if os.path.isfile(baseDir + '/webserver/login.txt'):
        # custom login message
        with open(baseDir + '/webserver/login.txt', 'r') as file:
            loginText = '<p class="login-text">' + file.read() + '</p>'

    cssFilename = baseDir + '/webserver/login.css'
    with open(cssFilename, 'r') as cssFile:
        loginCSS = cssFile.read()

    # show the register button
    registerButtonStr = ''
    if registrationsOpen:
        if registrationsRemaining > 0:
            idx = 'Welcome. Please login or register a new account.'
            loginText = \
                '<p class="login-text">' + idx + '</p>'
            registerButtonStr = \
                '<button type="submit" name="register">Register</button>'

    TOSstr = \
        '<p class="login-text"><a href="/terms">' + \
        'Terms of Service' + '</a></p>'
    TOSstr += \
        '<p class="login-text"><a href="/about">' + \
        'About this Instance' + '</a></p>'

    loginButtonStr = ''
    if accounts > 0:
        loginButtonStr = \
            '<button type="submit" name="submit">' + \
            'Login' + '</button>'

    autocompleteStr = ''
    if not autocomplete:
        autocompleteStr = 'autocomplete="off" value=""'

    loginForm = htmlHeader(cssFilename, loginCSS)
    loginForm += '<form method="POST" action="/login">'
    loginForm += '  <div class="imgcontainer">'
    loginForm += \
        '    <img loading="lazy" src="login.png' + \
        '" alt="login image" class="loginimage">'
    loginForm += loginText + TOSstr
    loginForm += '  </div>'
    loginForm += ''
    loginForm += '  <div class="container">'
    loginForm += '    <label for="nickname"><b>' + \
        'Nickname' + '</b></label>'
    loginForm += \
        '    <input type="text" ' + autocompleteStr + ' placeholder="' + \
        'Enter Nickname' + '" name="username" required autofocus>'
    loginForm += ''
    loginForm += '    <label for="password"><b>' + \
        'Password' + '</b></label>'
    loginForm += \
        '    <input type="password" ' + autocompleteStr + \
        ' placeholder="' + 'Enter Password' + \
        '" name="password" required>'
    loginForm += registerButtonStr + loginButtonStr
    loginForm += '  </div>'
    loginForm += '</form>'
    loginForm += \
        '<a href="https://gitlab.com/bashrc2/AberMUSH">' + \
        '<img loading="lazy" class="license" title="' + \
        'Get the source code' + '" alt="' + \
        'Get the source code' + '" src="/icons/agpl.png" /></a>'
    loginForm += htmlFooter()
    return loginForm


def createSession(onionRoute: bool):
    session = requests.session()
    if onionRoute:
        session.proxies = {}
        session.proxies['http'] = 'socks5h://localhost:9050'
        session.proxies['https'] = 'socks5h://localhost:9050'
    return session


def loadBrowserTokens(baseDir: str, tokensDict: {}, tokensLookup: {}) -> None:
    for subdir, dirs, files in os.walk(baseDir + '/players'):
        for playerFilename in files:
            tokenFilename = baseDir + '/players/' + playerFilename + '.token'
            if not os.path.isfile(tokenFilename):
                continue
            nickname = playerFilename.split('.')[0]
            token = None
            try:
                with open(tokenFilename, 'r') as fp:
                    token = fp.read()
            except Exception as e:
                print('WARN: Unable to read token for ' +
                      nickname + ' ' + str(e))
            if not token:
                continue
            tokensDict[nickname] = token
            tokensLookup[token] = nickname


class PubServer(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def _login_headers(self, fileFormat: str, length: int,
                       callingDomain: str) -> None:
        self.send_response(200)
        self.send_header('Content-type', fileFormat)
        self.send_header('Content-Length', str(length))
        self.send_header('Host', callingDomain)
        self.send_header('WWW-Authenticate',
                         'title="Login to AberMUSH", Basic realm="abermush"')
        self.send_header('X-Robots-Tag', 'noindex')
        self.end_headers()

    def _logout_headers(self, fileFormat: str, length: int,
                        callingDomain: str) -> None:
        self.send_response(200)
        self.send_header('Content-type', fileFormat)
        self.send_header('Content-Length', str(length))
        self.send_header('Set-Cookie', 'abermush=; SameSite=Strict')
        self.send_header('Host', callingDomain)
        self.send_header('WWW-Authenticate',
                         'title="Login to AberMUSH", Basic realm="abermush"')
        self.send_header('X-Robots-Tag', 'noindex')
        self.end_headers()

    def _set_headers_base(self, fileFormat: str, length: int, cookie: str,
                          callingDomain: str) -> None:
        self.send_response(200)
        self.send_header('Content-type', fileFormat)
        if length > -1:
            self.send_header('Content-Length', str(length))
        if cookie:
            self.send_header('Cookie', cookie)
        self.send_header('Host', callingDomain)
        self.send_header('X-Robots-Tag', 'noindex')
        self.send_header('Accept-Ranges', 'none')

    def _set_headers(self, fileFormat: str, length: int, cookie: str,
                     callingDomain: str) -> None:
        self._set_headers_base(fileFormat, length, cookie, callingDomain)
        self.send_header('Cache-Control', 'public, max-age=0')
        self.end_headers()

    def _set_headers_head(self, fileFormat: str, length: int, etag: str,
                          callingDomain: str) -> None:
        self._set_headers_base(fileFormat, length, None, callingDomain)
        if etag:
            self.send_header('ETag', etag)
        self.end_headers()

    def _set_headers_etag(self, mediaFilename: str, fileFormat: str,
                          data, cookie: str, callingDomain: str) -> None:
        self._set_headers_base(fileFormat, len(data), cookie, callingDomain)
        self.send_header('Cache-Control', 'public, max-age=86400')
        etag = None
        if os.path.isfile(mediaFilename + '.etag'):
            try:
                with open(mediaFilename + '.etag', 'r') as etagFile:
                    etag = etagFile.read()
            except BaseException:
                pass
        if not etag:
            etag = sha1(data).hexdigest()
            try:
                with open(mediaFilename + '.etag', 'w') as etagFile:
                    etagFile.write(etag)
            except BaseException:
                pass
        if etag:
            self.send_header('ETag', etag)
        self.end_headers()

    def _etag_exists(self, mediaFilename: str) -> bool:
        """Does an etag header exist for the given file?
        """
        etagHeader = 'If-None-Match'
        if not self.headers.get(etagHeader):
            etagHeader = 'if-none-match'
            if not self.headers.get(etagHeader):
                etagHeader = 'If-none-match'

        if self.headers.get(etagHeader):
            oldEtag = self.headers['If-None-Match']
            if os.path.isfile(mediaFilename + '.etag'):
                # load the etag from file
                currEtag = ''
                try:
                    with open(mediaFilename, 'r') as etagFile:
                        currEtag = etagFile.read()
                except BaseException:
                    pass
                if oldEtag == currEtag:
                    # The file has not changed
                    return True
        return False

    def _redirect_headers(self, redirect: str, cookie: str,
                          callingDomain: str) -> None:
        self.send_response(303)
        if cookie:
            self.send_header('Cookie', cookie)
        if '://' not in redirect:
            print('REDIRECT ERROR: redirect is not an absolute url ' +
                  redirect)
        self.send_header('Location', redirect)
        self.send_header('Host', callingDomain)
        self.send_header('Content-Length', '0')
        self.send_header('X-Robots-Tag', 'noindex')
        self.end_headers()

    def _httpReturnCode(self, httpCode: int, httpDescription: str) -> None:
        msg = "<html><head></head><body><h1>" + str(httpCode) + " " + \
            httpDescription + "</h1></body></html>"
        msg = msg.encode('utf-8')
        self.send_response(httpCode)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(msg)))
        self.send_header('X-Robots-Tag', 'noindex')
        self.end_headers()
        try:
            self.wfile.write(msg)
        except Exception as e:
            print('Error when showing ' + str(httpCode))
            print(e)

    def _200(self) -> None:
        self._httpReturnCode(200, 'Ok')

    def _404(self) -> None:
        self._httpReturnCode(404, 'Not Found')

    def _304(self) -> None:
        self._httpReturnCode(304, 'Resource has not changed')

    def _400(self) -> None:
        self._httpReturnCode(400, 'Bad Request')

    def _503(self) -> None:
        self._httpReturnCode(503, 'Service Unavailable')

    def _write(self, msg) -> None:
        tries = 0
        while tries < 5:
            try:
                self.wfile.write(msg)
                break
            except Exception as e:
                print(e)
                time.sleep(1)
                tries += 1

    def _robotsTxt(self) -> bool:
        if not self.path.lower().startswith('/robot'):
            return False
        msg = 'User-agent: *\nDisallow: /'
        msg = msg.encode('utf-8')
        self._set_headers('text/plain; charset=utf-8', len(msg),
                          None, self.server.domainFull)
        self._write(msg)
        return True

    def _clearLoginDetails(self, nickname: str):
        """Clears login details for the given account
        """
        # remove any token
        if self.server.tokens.get(nickname):
            del self.server.tokensLookup[self.server.tokens[nickname]]
            del self.server.tokens[nickname]
        self.send_response(303)
        self.send_header('Content-Length', '0')
        self.send_header('Set-Cookie', 'abermush=; SameSite=Strict')
        self.send_header('Location',
                         self.server.httpPrefix + '://' +
                         self.server.domainFull + '/login')
        self.send_header('X-Robots-Tag', 'noindex')
        self.end_headers()

    def _isAuthorized(self) -> bool:
        if self.path.startswith('/favicon.ico'):
            return False

        # token based authenticated used by the web interface
        if not self.headers.get('Cookie'):
            return False
        if self.headers['Cookie'].startswith('abermush='):
            tokenStr = self.headers['Cookie'].split('=', 1)[1].strip()
            if ';' in tokenStr:
                tokenStr = tokenStr.split(';')[0].strip()
            if self.server.tokensLookup.get(tokenStr):
                nickname = self.server.tokensLookup[tokenStr]
                playerFilename = \
                    self.server.baseDir + \
                    '/players/' + nickname + '.player'
                if os.path.isfile(playerFilename):
                    return True
                return False
            if self.server.debug:
                print('AUTH: abermush cookie ' +
                      'authorization failed, header=' +
                      self.headers['Cookie'].replace('abermush=', '') +
                      ' tokenStr=' + tokenStr + ' tokens=' +
                      str(self.server.tokensLookup))
            return False
        print('AUTH: Header cookie was not authorized')
        return False

    def _requestHTTP(self) -> bool:
        """Should a http response be given?
        """
        if not self.headers.get('Accept'):
            return False
        if self.server.debug:
            print('ACCEPT: ' + self.headers['Accept'])
        if 'image/' in self.headers['Accept']:
            if 'text/html' not in self.headers['Accept']:
                return False
        if 'video/' in self.headers['Accept']:
            if 'text/html' not in self.headers['Accept']:
                return False
        if 'audio/' in self.headers['Accept']:
            if 'text/html' not in self.headers['Accept']:
                return False
        if self.headers['Accept'].startswith('*'):
            return False
        if 'json' in self.headers['Accept']:
            return False
        return True

    def do_GET(self):
        callingDomain = self.server.domainFull
        if self.headers.get('Host'):
            callingDomain = self.headers['Host']
            if self.server.onionDomain:
                if callingDomain != self.server.domain and \
                   callingDomain != self.server.domainFull and \
                   callingDomain != self.server.onionDomain:
                    print('GET domain blocked: ' + callingDomain)
                    self._400()
                    return
            else:
                if callingDomain != self.server.domain and \
                   callingDomain != self.server.domainFull:
                    print('GET domain blocked: ' + callingDomain)
                    self._400()
                    return

        GETstartTime = time.time()

        if self.path == '/logout':
            msg = \
                htmlLogin(self.server.baseDir, False).encode('utf-8')
            self._logout_headers('text/html', len(msg), callingDomain)
            self._write(msg)
            return

        if self.server.debug:
            print('DEBUG: GET from ' + self.server.baseDir +
                  ' path: ' + self.path + ' busy: ' +
                  str(self.server.GETbusy))

        if self.server.debug:
            print(str(self.headers))

        cookie = None
        if self.headers.get('Cookie'):
            cookie = self.headers['Cookie']

        # check authorization
        authorized = self._isAuthorized()
        if self.server.debug:
            if authorized:
                print('GET Authorization granted')
            else:
                print('GET Not authorized')

        if not self.server.session:
            print('Starting new session')
            self.server.session = createSession(self.server.useTor)

        # is this a html request?
        htmlGET = False
        if self.headers.get('Accept'):
            if self._requestHTTP():
                htmlGET = True
        else:
            if self.headers.get('Connection'):
                # https://developer.mozilla.org/en-US/
                # docs/Web/HTTP/Protocol_upgrade_mechanism
                if self.headers.get('Upgrade'):
                    print('HTTP Connection request: ' +
                          self.headers['Upgrade'])
                else:
                    print('HTTP Connection request: ' +
                          self.headers['Connection'])
                self._200()
            else:
                print('WARN: No Accept header ' + str(self.headers))
                self._400()
            return


def runWebServer(baseDir: str, domain: str, onionDomain: str,
                 debug: bool, port=80, proxyPort=80,
                 httpPrefix='https', useTor=False) -> None:
    if len(domain) == 0:
        domain = 'localhost'
    if '.' not in domain:
        if domain != 'localhost':
            print('Invalid domain: ' + domain)
            return

    serverAddress = ('', proxyPort)
    pubHandler = partial(PubServer)

    try:
        httpd = ThreadingHTTPServer(serverAddress, pubHandler)
    except Exception as e:
        if e.errno == 98:
            print('ERROR: HTTP server address is already in use. ' +
                  str(serverAddress))
            return

        print('ERROR: HTTP server failed to start. ' + str(e))
        return

    httpd.onionDomain = onionDomain
    httpd.maxMessageLength = 32000
    httpd.domain = domain
    httpd.port = port
    httpd.domainFull = domain
    if port:
        if port != 80 and port != 443:
            if ':' not in domain:
                httpd.domainFull = domain + ':' + str(port)
    httpd.httpPrefix = httpPrefix
    httpd.debug = debug
    httpd.baseDir = baseDir
    httpd.useTor = useTor
    httpd.session = None
    httpd.sessionLastUpdate = 0
    httpd.lastGET = 0
    httpd.lastPOST = 0
    httpd.GETbusy = False
    httpd.POSTbusy = False
    httpd.tokens = {}
    httpd.tokensLookup = {}
    httpd.iconsCache = {}

    loadBrowserTokens(baseDir, httpd.tokens, httpd.tokensLookup)

    print('Running AberMUSH web server on ' +
          domain + ' port ' + str(proxyPort))
    httpd.serve_forever()
