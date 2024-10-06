import argparse
import os
import socket
from threading import *
class Connection(Thread):
    def __init__(self, socket, address):
        super().__init__()
        self.sock = socket
        self.addr = address
        self.start()
    def run(self):
        print(f"Started thread with {self.addr}")
        resp = self.req().decode().splitlines()
        req_type, path, http_ver = resp[0].split(" ")
        parsed_headers = dict(line.split(": ", 1) for line in resp[1:-2])
        if path == "/":
            self.resp(["HTTP/1.1 200 OK", "", ""])
        elif path.startswith("/echo/"):
            self.resp(
                [
                    "HTTP/1.1 200 OK",
                    "Content-Type: text/plain",
                    f"Content-Length: " + str(len(path[6:])),
                    "",
                    path[6:],
                ]
            )
        elif path == "/user-agent":
            self.resp(
                [
                    "HTTP/1.1 200 OK",
                    "Content-Type: text/plain",
                    f'Content-Length: {len(parsed_headers["User-Agent"])}',
                    "",
                    parsed_headers["User-Agent"],
                ]
            )
        # elif path.startswith('/list-files/'):
        #    dir_content = os.listdir(args.directory)
        #    print(dir_content)
        #    data = [i for i in dir_content]
        #    print(map(len, data))
        #    self.resp(
        #        ['HTTP/1.1 200 OK', 'Content-Type: text/plain', f'Content-Length: {len(data)}',
        #         '', '\r\n'.join(data)])
        elif path.startswith("/files/"):
            
                 print(os.listdir(args.directory))
                 print(os.path.join(args.directory, path[7:]))
                 
                 if os.path.exists(os.path.join(args.directory, path[7:])):
                   with open(os.path.join(args.directory, path[7:]), "r") as f:
                    file_content = f.read()
                   self.resp(
                    [
                        "HTTP/1.1 200 OK",
                        
                        "Content-Type: application/octet-stream",
                        f"Content-Length: {len(file_content)}",
                        "",
                        file_content,
                    ]
                )
                 else:
                  self.resp(
                    [
                        "HTTP/1.1 404",
                        "Content-Type: text/plain",
                        f"Content-Length: 3",
                        "",
                        "404",
                    ]
                )
        else:
            self.resp(
                [
                    "HTTP/1.1 404",
                    "Content-Type: text/plain",
                    f"Content-Length: 3",
                    "",
                    "404",
                ]
            )
    def req(self):
        return self.sock.recv(1024)
    def resp(self, args: list):
        print("------------")
        print("\r\n".join(args))
        print("------------")
        self.sock.send("\r\n".join(args).encode())
def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    while True:
        client, client_addr = server_socket.accept()  # wait for client
        Connection(client, client_addr)
if __name__ == "__main__":
    parse = argparse.ArgumentParser()
    parse.add_argument("--directory", required=False)
    args = parse.parse_args()
    main()