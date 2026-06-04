#!/usr/bin/env python3
from __future__ import annotations

import argparse
import threading
import webbrowser
from http.server import ThreadingHTTPServer

from combined_null_4nf_frontend import Handler


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Launch the Relational Database Normaliser desktop app."
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument(
        "--port",
        type=int,
        default=0,
        help="Port to bind. Use 0 to choose an available port.",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Start the local server without opening a browser.",
    )
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    host, port = server.server_address[:2]
    url = f"http://{host}:{port}"
    print(f"Serving Normaliser at {url}")

    if not args.no_browser:
        threading.Timer(0.4, webbrowser.open_new, args=(url,)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
