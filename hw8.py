from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
import os
from requests import get, put
import urllib.parse
import json


class YandexDiskClient:
    def __init__(self, token):
        self.oauth_token = token

    def get_file_names(self, path):
        resp = get(f"https://cloud-api.yandex.net/v1/disk/resources?path={path}",
                   headers={"Authorization": f"OAuth {self.oauth_token}"})
        data = json.loads(resp.text)
        file_names = list(map(lambda file: file["name"], data["_embedded"]["items"]))
        return file_names

    def upload_file(self, file_name, local_path, dist_path):
        resp = get(f"https://cloud-api.yandex.net/v1/disk/resources/upload?path={dist_path}",
                   headers={"Authorization": f"OAuth {self.oauth_token}"})
        upload_url = json.loads(resp.text)["href"]
        put(upload_url, files={'file': (file_name, open(local_path, 'rb'))})


oauth_token = os.environ['YA_TOKEN']
ya_disk_client = YandexDiskClient(oauth_token)


class HttpGetHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        file_names = ya_disk_client.get_file_names('Backup')
        def fname2html(fname):
            style = "background-color: rgba(0, 200, 0, 0.25)" if fname in file_names else ""
            return f"""
                <li style="{style}" onclick="fetch('/upload', {{'method': 'POST', 'body': '{fname}'}})">
                    {fname}
                </li>
            """

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write("""
            <html>
                <head>
                </head>
                <body>
                    <ul>
                      {files}
                    </ul>
                </body>
            </html>
        """.format(files="\n".join(map(fname2html, os.listdir("pdfs")))).encode())

    def do_POST(self):
        content_len = int(self.headers.get('Content-Length'))
        fname = self.rfile.read(content_len).decode("utf-8")

        local_path = f"pdfs/{fname}"
        ya_path = f"Backup/{urllib.parse.quote(fname)}"

        ya_disk_client.upload_file(fname, local_path, ya_path)
        self.send_response(200)
        self.end_headers()


def run(handler_class=BaseHTTPRequestHandler):
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, handler_class)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()


run(handler_class=HttpGetHandler)