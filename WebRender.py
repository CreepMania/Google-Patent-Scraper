from PyQt5 import QtCore
from PyQt5.QtWebEngineCore import QWebEngineHttpRequest
from PyQt5.QtWebEngineWidgets import QWebEngineView
from fake_useragent import UserAgent,FakeUserAgentError


def render(url, app):
    """Fully render HTML, JavaScript and all."""

    class Render(QWebEngineView):
        def __init__(self, website_url):
            self.html = None
            self.app = app
            QWebEngineView.__init__(self)
            self.loadFinished.connect(self._loadFinished)

            """spoofing html header to request the server multiple times, Google will most likely block it otherwise"""
            try:
                ua = UserAgent(fallback='firefox')
                ua = ua.random
            except FakeUserAgentError as e:
                print('No user agent available: ' + str(e))

            """setting the httpRequest with our spoofed header and sending it"""
            req = QWebEngineHttpRequest(QtCore.QUrl(website_url))
            req.setUrl(QtCore.QUrl(website_url))
            req.setHeader(bytearray("header", 'utf-8'), bytearray(ua, 'utf-8'))
            self.load(req)
            while self.html is None:
                self.app.processEvents(QtCore.QEventLoop.ExcludeUserInputEvents |
                                       QtCore.QEventLoop.ExcludeSocketNotifiers |
                                       QtCore.QEventLoop.WaitForMoreEvents)

        def _callable(self, data):
            self.html = data

        def _loadFinished(self):
            self.page().toHtml(self._callable)

    return Render(url).html
