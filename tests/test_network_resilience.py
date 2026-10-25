from tools.network import MAX_RESPONSE_BYTES, http_get


def test_http_get_uses_bounded_range_for_oversized_response(monkeypatch):
    class Headers:
        def __init__(self, content_length=None, content_range=None):
            self.content_length = content_length
            self.content_range = content_range

        def get(self, name):
            if name == "Content-Length":
                return self.content_length
            if name == "Content-Range":
                return self.content_range
            return None

        def get_content_charset(self):
            return "utf-8"

    class Response:
        def __init__(self, headers, payload):
            self.headers = headers
            self.payload = payload

        def read(self, limit):
            return self.payload[:limit]

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class Opener:
        def __init__(self):
            self.requests = []

        def open(self, request, timeout):
            self.requests.append(request)
            if request.headers.get("Range"):
                return Response(
                    Headers(str(MAX_RESPONSE_BYTES), f"bytes 0-{MAX_RESPONSE_BYTES - 1}/100000"),
                    b"A" * MAX_RESPONSE_BYTES,
                )
            return Response(Headers(str(MAX_RESPONSE_BYTES + 1000)), b"")

    opener = Opener()
    monkeypatch.setattr("tools.network._validate_public_url", lambda _url: ("example.com", 443))
    monkeypatch.setattr("tools.network.build_opener", lambda *_args, **_kwargs: opener)

    result = http_get("https://example.com")

    assert result.startswith("[BEGIN UNTRUSTED WEB CONTENT]")
    assert "partial page fetched" in result
    assert any(request.headers.get("Range") == f"bytes=0-{MAX_RESPONSE_BYTES - 1}" for request in opener.requests)


def test_http_get_avoids_range_when_response_is_within_limit(monkeypatch):
    class Headers:
        def get(self, name):
            if name == "Content-Length":
                return "4"
            return None

        def get_content_charset(self):
            return "utf-8"

    class Response:
        headers = Headers()

        def read(self, _limit):
            return b"test"

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class Opener:
        def __init__(self):
            self.requests = []

        def open(self, request, timeout):
            self.requests.append(request)
            return Response()

    opener = Opener()
    monkeypatch.setattr("tools.network._validate_public_url", lambda _url: ("example.com", 443))
    monkeypatch.setattr("tools.network.build_opener", lambda *_args, **_kwargs: opener)

    result = http_get("https://example.com")

    assert result.endswith("test\n[END UNTRUSTED WEB CONTENT]")
    assert not opener.requests[0].headers.get("Range")
