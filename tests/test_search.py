from tools.search import web_search


def test_web_search_rejects_empty_query():
    result = web_search("")
    assert result == "Search denied: a query is required."


def test_web_search_rejects_oversized_query():
    result = web_search("x" * 301)
    assert result == "Search denied: query is too long."


def test_web_search_wraps_results_as_untrusted(monkeypatch):
    class FakeHeaders:
        def get(self, name):
            return None

        def get_content_charset(self):
            return "utf-8"

    class FakeResponse:
        headers = FakeHeaders()

        def read(self, _limit):
            return (
                b'<a class="result-link" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com">'
                b'Example Result</a>'
            )

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(
        "tools.search.urlopen",
        lambda request, timeout: FakeResponse(),
    )

    result = web_search("example")

    assert result.startswith("[BEGIN UNTRUSTED WEB SEARCH RESULTS]")
    assert "1. Example Result" in result
    assert "URL: https://example.com" in result
    assert result.endswith("[END UNTRUSTED WEB SEARCH RESULTS]")
