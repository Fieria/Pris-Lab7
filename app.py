from http.server import BaseHTTPRequestHandler, HTTPServer
import os

class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        # Возвращает имя пода, чтобы мы видели работу балансировщика
        pod_name = os.getenv('POD_NAME', 'Unknown Pod')
        self.wfile.write(f"<h1>Привет из Kubernetes!</h1><p>Привет от пода: {pod_name}</p>".encode())

server = HTTPServer(('0.0.0.0', 8080), MyHandler)
print("Сервер запущен на порту 8080...")
server.serve_forever()
