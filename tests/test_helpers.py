import contextlib
import socket
import time
import webbrowser

from nicegui import helpers


def test_is_port_open():
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(('127.0.0.1', 0))  # port = 0 => the OS chooses a port for us
        sock.listen(1)
        host, port = sock.getsockname()
    assert not helpers.is_port_open(host, port), 'after closing the socket, the port should be free'

    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(('127.0.0.1', port))
        sock.listen(1)
        assert helpers.is_port_open(host, port), 'after opening the socket, the port should be detected'


def test_schedule_browser(monkeypatch):

    called_with_url = None

    def mock_webbrowser_open(url):
        nonlocal called_with_url
        called_with_url = url

    monkeypatch.setattr(webbrowser, 'open', mock_webbrowser_open)

    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:

        sock.bind(('127.0.0.1', 0))
        host, port = sock.getsockname()

        thread, cancel_event = helpers.schedule_browser(host, port)

        try:
            # port bound, but not opened yet
            assert called_with_url is None

            sock.listen()
            # port opened
            time.sleep(1)
            assert called_with_url == f'http://{host}:{port}/'
        finally:
            cancel_event.set()


def test_canceling_schedule_browser(monkeypatch):

    called_with_url = None

    def mock_webbrowser_open(url):
        nonlocal called_with_url
        called_with_url = url

    monkeypatch.setattr(webbrowser, 'open', mock_webbrowser_open)

    # find a free port ...
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('127.0.0.1', 0))
    sock.listen(1)
    host, port = sock.getsockname()
    # ... and close it so schedule_browser does not launch the browser
    sock.close()

    thread, cancel_event = helpers.schedule_browser(host, port)
    time.sleep(0.2)
    cancel_event.set()
    time.sleep(0.2)
    assert not thread.is_alive()
    assert called_with_url is None
