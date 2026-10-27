"""
libromorph.server: Local HTTP preview server for testing generated HTML ebook websites.
"""

import http.server
import socketserver
import os
import sys
import webbrowser


def run_preview_server(serve_dir: str, port: int = 8000, open_browser: bool = False):
    serve_dir = os.path.abspath(serve_dir)
    if not os.path.exists(serve_dir):
        print(f"Error: Directory '{serve_dir}' does not exist.")
        sys.exit(1)

    os.chdir(serve_dir)
    handler = http.server.SimpleHTTPRequestHandler

    # Enable socket reuse
    socketserver.TCPServer.allow_reuse_address = True

    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            url = f"http://localhost:{port}"
            print(f"\n========================================================")
            print(f"  LibroMorph Book Preview Server Active")
            print(f"  Serving: {serve_dir}")
            print(f"  URL:     {url}")
            print(f"  Press Ctrl+C to stop.")
            print(f"========================================================\n")
            if open_browser:
                webbrowser.open(url)
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[LibroMorph] Preview server stopped.")
    except OSError as e:
        print(f"\n[LibroMorph] Could not start server on port {port}: {e}")
