"""One-request loopback relay: actual HTTP faults, never hosted transport."""
import http.client
import json
import re
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

ORIGINS = ('http://127.0.0.1:59999', 'http://127.0.0.1:54321/auth/v1')
BODY_LIMIT = 65536


class UnknownOutcome(Exception):
    def __init__(self, terminal=False):
        super().__init__('auth_failure_http_unknown')
        self.terminal = terminal


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise UnknownOutcome()


class StrictHTTPResponse(http.client.HTTPResponse):
    def _read_and_discard_trailer(self):
        # stdlib tolerates EOF here. Terminal proof requires the final CRLF,
        # while the standard chunk decoder still parses all chunk sizes/data.
        remaining = 16384
        while remaining:
            line = self.fp.readline(remaining + 1)
            if not line or len(line) > remaining or not line.endswith(b'\r\n'):
                raise http.client.IncompleteRead(b'')
            remaining -= len(line)
            if line == b'\r\n':
                return
        raise http.client.IncompleteRead(b'')


class StrictHTTPConnection(http.client.HTTPConnection):
    response_class = StrictHTTPResponse


class StrictHTTPHandler(urllib.request.HTTPHandler):
    def http_open(self, request):
        return self.do_open(StrictHTTPConnection, request)


def complete_body(response):
    """Bounded read alone silently accepts a short Content-Length response."""
    lengths = response.headers.get_all('Content-Length', [])
    encodings = response.headers.get_all('Transfer-Encoding', [])
    if len(lengths) > 1 or len(encodings) > 1 or (lengths and encodings):
        raise UnknownOutcome()
    expected = None
    if lengths:
        if not re.fullmatch(r'[0-9]+', lengths[0].strip()):
            raise UnknownOutcome()
        expected = int(lengths[0])
        if expected > BODY_LIMIT:
            raise UnknownOutcome()
    elif encodings:
        if encodings[0].strip().lower() != 'chunked':
            raise UnknownOutcome()
    elif response.status not in (204, 304):
        # EOF-delimited bodies do not supply the affirmative framing witness.
        raise UnknownOutcome()
    body = response.read(BODY_LIMIT + 1)
    if (len(body) > BODY_LIMIT or (expected is not None and len(body) != expected)
            or (response.status in (204, 304) and body)):
        raise UnknownOutcome()
    # With chunked encoding, reading beyond the entire accepted body forces
    # http.client to consume the terminating chunk; truncation raises HTTPException.
    return body


class LocalTransport:
    def __init__(self, origin, admin_token, api_key=None):
        if origin not in ORIGINS or not isinstance(admin_token, str) or not admin_token:
            raise ValueError('auth_failure_local_credentials_required')
        self.origin, self.admin_token, self.api_key = origin, admin_token, api_key

    def __repr__(self):
        return '<LocalTransport loopback credentials redacted>'

    def request(self, method, path, data=None, token=None, fault=None):
        if fault not in (None, 'lost_reply', 'timeout'):
            raise ValueError('auth_failure_fault')
        if not (path in ('/admin/users', '/token?grant_type=password', '/logout?scope=global')
                or (method == 'DELETE' and path.startswith('/admin/users/'))):
            raise ValueError('auth_failure_path')
        if path.startswith('/admin/users/'):
            import uuid
            if str(uuid.UUID(path[13:])) != path[13:]:
                raise ValueError('auth_failure_user_path')
        headers = {'Content-Type': 'application/json'}
        bearer = self.admin_token if path.startswith('/admin/users') else token
        if bearer:
            headers['Authorization'] = 'Bearer ' + bearer
        if self.api_key:
            headers['apikey'] = self.api_key
        payload = None if data is None else json.dumps(data).encode()
        upstream = urllib.request.Request(self.origin + path, data=payload, headers=headers, method=method)
        terminal = threading.Event()
        release = threading.Event()
        done = threading.Event()
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect(), StrictHTTPHandler())

        class Relay(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                try:
                    try:
                        response = opener.open(upstream, timeout=5)
                    except urllib.error.HTTPError as error:
                        response = error
                    with response:
                        status, body = response.status, complete_body(response)
                    # Only a complete upstream response proves this mint worker terminal.
                    terminal.set()
                    if fault == 'lost_reply':
                        return
                    if fault == 'timeout':
                        release.wait(5)
                        return
                    self.send_response(status)
                    self.send_header('Content-Length', str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                except (OSError, http.client.HTTPException, UnknownOutcome, ValueError):
                    pass
                finally:
                    done.set()

        server = HTTPServer(('127.0.0.1', 0), Relay)
        server.timeout = 5
        worker = threading.Thread(target=server.handle_request, daemon=True)
        worker.start()
        client = http.client.HTTPConnection('127.0.0.1', server.server_port,
                                            timeout=0.2 if fault == 'timeout' else 5)
        try:
            client.request('POST', '/')
            response = client.getresponse()
            body = complete_body(response)
            return {'status': response.status, 'body': json.loads(body) if body else {},
                    'terminal': terminal.is_set()}
        except (OSError, http.client.HTTPException, ValueError):
            release.set()
            worker.join(5)
            raise UnknownOutcome(terminal.is_set() and done.is_set()) from None
        finally:
            release.set()
            client.close()
            worker.join(5)
            server.server_close()
