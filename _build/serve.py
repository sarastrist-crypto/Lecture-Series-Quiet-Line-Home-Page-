#!/usr/bin/env python3
"""Static HTTP server with byte-range support for <video> streaming."""
import http.server, os, sys, re, mimetypes

ROOT = os.path.abspath(os.environ.get("SERVE_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PORT = int(os.environ.get("SERVE_PORT", "8000"))

class RangeHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        # Map / to /index.html
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            for idx in ("index.html", "index.htm"):
                cand = os.path.join(path, idx)
                if os.path.exists(cand):
                    path = cand; break
            else:
                return super().do_GET()

        if not os.path.exists(path):
            self.send_error(404)
            return

        size = os.path.getsize(path)
        ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
        rng = self.headers.get("Range")

        if rng:
            m = re.match(r"bytes=(\d*)-(\d*)$", rng)
            if not m:
                self.send_error(416, "Invalid Range")
                return
            start_s, end_s = m.groups()
            if start_s == "" and end_s == "":
                self.send_error(416); return
            if start_s == "":
                length = int(end_s)
                start = max(0, size - length); end = size - 1
            else:
                start = int(start_s)
                end = int(end_s) if end_s else size - 1
            if start >= size or end >= size:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{size}")
                self.end_headers(); return

            length = end - start + 1
            self.send_response(206)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(length))
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.send_header("Accept-Ranges", "bytes")
            self.end_headers()
            with open(path, "rb") as f:
                f.seek(start)
                remaining = length
                chunk = 64 * 1024
                while remaining > 0:
                    buf = f.read(min(chunk, remaining))
                    if not buf: break
                    try:
                        self.wfile.write(buf)
                    except (BrokenPipeError, ConnectionResetError):
                        return
                    remaining -= len(buf)
            return

        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(size))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        with open(path, "rb") as f:
            self.copyfile(f, self.wfile)

    def log_message(self, fmt, *a):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % a))

if __name__ == "__main__":
    print(f"Serving {ROOT} on http://localhost:{PORT}", file=sys.stderr)
    http.server.ThreadingHTTPServer(("", PORT), RangeHandler).serve_forever()
