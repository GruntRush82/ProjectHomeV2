"""E2E test fixtures for Playwright browser tests.

These fixtures start a live Flask dev server and provide a Playwright
browser page pointed at it. Each test gets a fresh database.
"""
import pytest
import threading
import socket


def _find_free_port():
    """Find a free port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure Playwright browser context for all E2E tests."""
    return {
        **browser_context_args,
        "viewport": {"width": 1024, "height": 768},  # iPad landscape
        "ignore_https_errors": True,
    }


@pytest.fixture
def live_server(app):
    """Start a live Flask server in a background thread.

    Returns the base URL (e.g., 'http://127.0.0.1:5432').
    """
    port = _find_free_port()
    server_thread = threading.Thread(
        target=lambda: app.run(
            host="127.0.0.1",
            port=port,
            debug=False,
            use_reloader=False,
        ),
        daemon=True,
    )
    server_thread.start()

    # Wait for server to be ready
    import time

    for _ in range(50):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                break
        except OSError:
            time.sleep(0.1)

    yield f"http://127.0.0.1:{port}"


@pytest.fixture
def e2e_page(page, live_server):
    """Playwright page pointed at the live server.

    Usage:
        def test_login(e2e_page):
            e2e_page.goto("/")
            assert e2e_page.title() == "Felker Family Hub"
    """
    base_url = live_server

    class PageWithBase:
        """Wrapper that prepends base_url to relative paths."""

        def __init__(self, pw_page, base):
            self._page = pw_page
            self._base = base

        def goto(self, path, **kwargs):
            url = f"{self._base}{path}" if path.startswith("/") else path
            return self._page.goto(url, **kwargs)

        def __getattr__(self, name):
            return getattr(self._page, name)

    yield PageWithBase(page, base_url)
