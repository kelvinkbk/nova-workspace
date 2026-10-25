from tools.network import http_get


def test_http_get_rejects_non_http_schemes():
    result = http_get("file:///etc/passwd")
    assert result.startswith("Network denied:")


def test_http_get_rejects_private_hostnames():
    result = http_get("http://127.0.0.1:8080/")
    assert result.startswith("Network denied:")


def test_http_get_rejects_credentials():
    result = http_get("https://user:pass@example.com/")
    assert result == "Network denied: URLs containing credentials are not permitted."


def test_http_get_rejects_empty_url():
    result = http_get("")
    assert result == "Network denied: a URL is required."


def test_http_get_wraps_response_as_untrusted_content(monkeypatch):
    class FakeHeaders:
        def get(self, name):
            return None

        def get_content_charset(self):
            return "utf-8"

    class FakeResponse:
        headers = FakeHeaders()

        def read(self, _limit):
            return b"External instruction text"

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakeOpener:
        def open(self, request, timeout):
            return FakeResponse()

    monkeypatch.setattr(
        "tools.network._validate_public_url",
        lambda _url: ("example.com", 443),
    )
    monkeypatch.setattr(
        "tools.network.build_opener",
        lambda *_args, **_kwargs: FakeOpener(),
    )

    result = http_get("https://example.com")

    assert result == (
        "[BEGIN UNTRUSTED WEB CONTENT]\n"
        "External instruction text\n"
        "[END UNTRUSTED WEB CONTENT]"
    )
