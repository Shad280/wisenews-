import http.server
import socketserver
import os
from urllib.parse import urlparse, parse_qs
import json

class WiseNewsHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                'status': 'WiseNews is working!',
                'message': 'This is a basic HTTP server test',
                'server': 'Python built-in HTTP server',
                'timestamp': '2025-08-08'
            }
            self.wfile.write(json.dumps(response).encode())
        elif parsed_path.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                'status': 'healthy',
                'version': '1.0.0',
                'message': 'WiseNews basic server is running'
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {'error': 'Not found'}
            self.wfile.write(json.dumps(response).encode())

if __name__ == "__main__":
    PORT = int(os.environ.get('PORT', 5000))
    HOST = os.environ.get('HOST', '0.0.0.0')
    
    with socketserver.TCPServer((HOST, PORT), WiseNewsHandler) as httpd:
        print(f"Server running on {HOST}:{PORT}")
        httpd.serve_forever()
