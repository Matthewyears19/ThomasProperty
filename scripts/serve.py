"""Local static QA server. Does not send email or run Cloudflare Functions."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import argparse
import json
from urllib.parse import urlsplit

OUT = Path(__file__).resolve().parents[1] / 'dist'


class PreviewHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(OUT), **kwargs)

    def end_headers(self):
        header_file = OUT / '_headers'
        if header_file.exists():
            for line in header_file.read_text(encoding='utf-8').split('\n\n')[0].splitlines()[1:]:
                if line.startswith('  ') and ': ' in line:
                    name, value = line.strip().split(': ', 1)
                    self.send_header(name, value)
        super().end_headers()

    def do_GET(self):
        path = urlsplit(self.path).path
        if path in ('/api/form-config', '/api/analytics-config'):
            data = json.dumps({'enabled': False}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        super().do_GET()

    def send_error(self, code, message=None, explain=None):
        if code == 404 and (OUT / '404.html').is_file():
            data = (OUT / '404.html').read_bytes()
            self.send_response(404)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            if self.command != 'HEAD':
                self.wfile.write(data)
            return
        super().send_error(code, message, explain)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8000)
    arguments = parser.parse_args()
    print(f'Local static QA preview: http://127.0.0.1:{arguments.port}/ (enquiries/analytics disabled)', flush=True)
    ThreadingHTTPServer(('127.0.0.1', arguments.port), PreviewHandler).serve_forever()
