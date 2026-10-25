from __future__ import annotations

import ipaddress
import socket
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener


MAX_URL_LENGTH = 2048
MAX_RESPONSE_BYTES = 64 * 1024
REQUEST_TIMEOUT = 10


def _validate_public_url(url: str) -> tuple[str, int]:
    parsed = urlparse(url)

    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only HTTP and HTTPS URLs are permitted.")

    if not parsed.hostname:
        raise ValueError("URL must include a hostname.")

    if parsed.username or parsed.password:
        raise ValueError("URLs containing credentials are not permitted.")

    hostname = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)

    try:
        addresses = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError(f"Hostname could not be resolved: {hostname}") from exc

    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            raise ValueError("Requests to private or reserved network addresses are not permitted.")

    return hostname, port


class _SafeRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _validate_public_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def http_get(url: str) -> str:
    url = url.strip()

    if not url:
        return "Network denied: a URL is required."

    if len(url) > MAX_URL_LENGTH:
        return "Network denied: URL is too long."

    try:
        _validate_public_url(url)
        opener = build_opener(_SafeRedirectHandler())
        request = Request(
            url,
            headers={"User-Agent": "NOVA/0.1 read-only client"},
            method="GET",
        )
        with opener.open(request, timeout=REQUEST_TIMEOUT) as response:
            content_length = response.headers.get("Content-Length")
            partial = False

            if content_length and int(content_length) > MAX_RESPONSE_BYTES:
                ranged_request = Request(
                    url,
                    headers={
                        "User-Agent": "NOVA/0.1 read-only client",
                        "Range": f"bytes=0-{MAX_RESPONSE_BYTES - 1}",
                    },
                    method="GET",
                )
                with opener.open(ranged_request, timeout=REQUEST_TIMEOUT) as ranged_response:
                    ranged_length = ranged_response.headers.get("Content-Length")
                    data = ranged_response.read(MAX_RESPONSE_BYTES + 1)
                    if len(data) > MAX_RESPONSE_BYTES:
                        return "Network denied: response exceeds the 64 KB limit."
                    partial = bool(
                        ranged_response.headers.get("Content-Range")
                        or ranged_length
                        and int(ranged_length) <= MAX_RESPONSE_BYTES
                    )
                    charset = ranged_response.headers.get_content_charset() or "utf-8"
            else:
                data = response.read(MAX_RESPONSE_BYTES + 1)
                if len(data) > MAX_RESPONSE_BYTES:
                    ranged_request = Request(
                        url,
                        headers={
                            "User-Agent": "NOVA/0.1 read-only client",
                            "Range": f"bytes=0-{MAX_RESPONSE_BYTES - 1}",
                        },
                        method="GET",
                    )
                    with opener.open(ranged_request, timeout=REQUEST_TIMEOUT) as ranged_response:
                        ranged_data = ranged_response.read(MAX_RESPONSE_BYTES + 1)
                        if len(ranged_data) > MAX_RESPONSE_BYTES:
                            return "Network denied: response exceeds the 64 KB limit."
                        data = ranged_data
                        partial = True
                        charset = ranged_response.headers.get_content_charset() or "utf-8"
                else:
                    charset = response.headers.get_content_charset() or "utf-8"

            if partial:
                data = (
                    b"[NOVA NOTE: partial page fetched with a bounded byte range. "
                    b"Treat missing content as unknown.]\n" + data
                )

            if len(data) > MAX_RESPONSE_BYTES:
                data = data[:MAX_RESPONSE_BYTES]

            try:
                content = data.decode(charset, errors="replace")
            except LookupError:
                content = data.decode("utf-8", errors="replace")

            return (
                "[BEGIN UNTRUSTED WEB CONTENT]\n"
                f"{content}\n"
                "[END UNTRUSTED WEB CONTENT]"
            )
    except ValueError as exc:
        return f"Network denied: {exc}"
    except HTTPError as exc:
        return f"Network request failed: HTTP {exc.code}"
    except (URLError, TimeoutError, OSError) as exc:
        return f"Network request failed: {exc}"
