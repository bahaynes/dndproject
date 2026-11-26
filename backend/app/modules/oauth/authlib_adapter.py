"""A small Starlette/FastAPI adapter for Authlib's framework-agnostic AuthorizationServer.

Authlib ships server integrations only for Flask and Django; this mirrors the Flask
one. Starlette reads forms asynchronously, so the route reads the request first
(``await read_oauth2_request(request)``) and hands Authlib a plain OAuth2Request.
Responses come back as AuthlibResponse, which Authlib hooks (RFC 9207 ``iss``) can
edit through ``.location`` before the route turns it into a Starlette response.
"""
import json
from collections import defaultdict
from typing import Optional
from urllib.parse import urlencode

from authlib.oauth2 import AuthorizationServer
from authlib.oauth2.rfc6749 import OAuth2Payload, OAuth2Request
from starlette.requests import Request
from starlette.responses import Response


class StaticPayload(OAuth2Payload):
    def __init__(self, data: dict, datalist: dict):
        self._data = data
        self._datalist = datalist

    @property
    def data(self):
        return self._data

    @property
    def datalist(self):
        return self._datalist


class StaticOAuth2Request(OAuth2Request):
    """An OAuth2Request built from already-read query and form values."""

    def __init__(self, method: str, uri: str, headers, args: list[tuple[str, str]], form: list[tuple[str, str]]):
        super().__init__(method=method, uri=uri, headers=headers)
        self._args = dict(args)
        self._form = dict(form)
        datalist = defaultdict(list)
        for key, value in [*args, *form]:
            datalist[key].append(value)
        data = {**self._args, **self._form}
        self.payload = StaticPayload(data, datalist)

    @property
    def args(self):
        return self._args

    @property
    def form(self):
        return self._form


def build_request(method: str, uri: str, headers, args=(), form=()) -> StaticOAuth2Request:
    return StaticOAuth2Request(method, uri, headers, list(args), list(form))


async def read_oauth2_request(request: Request, public_origin: str) -> StaticOAuth2Request:
    """Reads query and (for POST) form values. The URI is rebuilt on the public origin:
    behind Caddy and Cloud Run the backend itself only ever sees plain http."""
    args = list(request.query_params.multi_items())
    form: list[tuple[str, str]] = []
    if request.method == "POST":
        parsed = await request.form()
        form = [(k, v) for k, v in parsed.multi_items() if isinstance(v, str)]
    uri = f"{public_origin}{request.url.path}"
    if args:
        uri = f"{uri}?{urlencode(args)}"
    return build_request(request.method, uri, dict(request.headers), args, form)


class AuthlibResponse:
    def __init__(self, status_code: int, body, headers):
        self.status_code = status_code
        self.body = body
        self.headers = list(headers or [])

    @property
    def location(self) -> Optional[str]:
        for key, value in self.headers:
            if key.lower() == "location":
                return value
        return None

    @location.setter
    def location(self, value: str) -> None:
        self.headers = [(k, v) for k, v in self.headers if k.lower() != "location"]
        self.headers.append(("Location", value))

    def to_starlette(self) -> Response:
        body = self.body
        if isinstance(body, (dict, list)):
            body = json.dumps(body)
        headers = {k: v for k, v in self.headers}
        return Response(content=body or b"", status_code=self.status_code, headers=headers)


class StarletteAuthorizationServer(AuthorizationServer):
    """AuthorizationServer that takes pre-read requests and returns AuthlibResponse objects."""

    def create_oauth2_request(self, request) -> OAuth2Request:
        if isinstance(request, OAuth2Request):
            return request
        raise TypeError("Pass the result of read_oauth2_request(); Starlette requests are read asynchronously.")

    def create_json_request(self, request):
        raise NotImplementedError("No JSON endpoints are registered.")

    def handle_response(self, status_code, payload, headers):
        return AuthlibResponse(status_code, payload, headers)

    def send_signal(self, name, *args, **kwargs):
        pass
