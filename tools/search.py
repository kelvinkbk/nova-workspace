from __future__ import annotations

from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote_plus, urlparse
from urllib.request import Request, urlopen


SEARCH_ENDPOINT = "https://lite.duckduckgo.com/lite/?q="
MAX_QUERY_LENGTH = 300
MAX_RESULTS = 5
REQUEST_TIMEOUT = 10
MAX_RESPONSE_BYTES = 128 * 1024


class _SearchResultParser(HTMLParser):
    """Extract DuckDuckGo Lite result links while ignoring page instructions."""

    def __init__(self) -> None:
        super().__init__()
        self.results: list[dict[str, str]] = []
        self._current_url: str | None = None
        self._title_parts: list[str] = []
        self._capture_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a" or len(self.results) >= MAX_RESULTS:
            return

        attributes = dict(attrs)
        classes = set((attributes.get("class") or "").split())

        if "result-link" in classes or "result__a" in classes:
            href = attributes.get("href") or ""
            if href:
                self._current_url = href
                self._title_parts = []
                self._capture_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag != "a" or not self._capture_title:
            return

        title = " ".join("".join(self._title_parts).split())
        if self._current_url and title:
            self.results.append(
                {
                    "title": title,
                    "url": self._current_url,
                }
            )

        self._current_url = None
        self._title_parts = []
        self._capture_title = False

    def handle_data(self, data: str) -> None:
        if self._capture_title:
            self._title_parts.append(data)


def web_search(query: str, limit: int = 5) -> str:
    query = query.strip()
    if not query:
        return "Search denied: a query is required."
    if len(query) > MAX_QUERY_LENGTH:
        return "Search denied: query is too long."

    limit = max(1, min(limit, MAX_RESULTS))
    url = SEARCH_ENDPOINT + quote_plus(query)

    try:
        request = Request(
            url,
            headers={"User-Agent": "NOVA/0.1 read-only search client"},
            method="GET",
        )
        with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > MAX_RESPONSE_BYTES:
                return "Search failed: response exceeds the 128 KB limit."

            data = response.read(MAX_RESPONSE_BYTES + 1)
            if len(data) > MAX_RESPONSE_BYTES:
                return "Search failed: response exceeds the 128 KB limit."

            charset = response.headers.get_content_charset() or "utf-8"
            try:
                html = data.decode(charset, errors="replace")
            except LookupError:
                html = data.decode("utf-8", errors="replace")

        parser = _SearchResultParser()
        parser.feed(html)
        results = parser.results[:limit]

        if not results:
            return f'No search results found for "{query}".'

        lines = [
            "[BEGIN UNTRUSTED WEB SEARCH RESULTS]",
            f"Query: {query}",
        ]
        for index, result in enumerate(results, start=1):
            result_url = result["url"]
            if result_url.startswith("//"):
                result_url = "https:" + result_url

            parsed_result = urlparse(result_url)
            redirect_target = parse_qs(parsed_result.query).get("uddg", [])
            if parsed_result.netloc == "duckduckgo.com" and redirect_target:
                result_url = redirect_target[0]

            lines.append(f"{index}. {result['title']}")
            lines.append(f"   URL: {result_url}")
        lines.append("[END UNTRUSTED WEB SEARCH RESULTS]")
        return "\n".join(lines)
    except HTTPError as exc:
        return f"Search failed: HTTP {exc.code}"
    except (URLError, TimeoutError, OSError) as exc:
        return f"Search failed: {exc}"
