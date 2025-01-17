import socket
from threading import Thread

def reply(req, code, body="", headers={}):
    b_reply = b""
    match code:
        case 200:
            b_reply += b"HTTP/1.1 200 OK\r\n"
        case 404:
            b_reply += b"HTTP/1.1 404 Not Found\r\n"
        case 500:
            b_reply += b"HTTP/1.1 500 Internal Server Error\r\n"
    if "Content-Type" not in headers:
        headers["Content-Type"] = "text/plain"
    if body:
        headers["Content-Length"] = str(len(body))
    for key, val in headers.items():
        b_reply += bytes(f"{key}: {val}", "utf-8") + b"\r\n"
    b_reply += b"\r\n" + bytes(body, "utf-8")
    return b_reply

def handle_request(req):
    if req["path"] == "/":
        return reply(req, 200)
    elif req["path"].startswith("/echo/"):
        return reply(req, 200, req["path"][6:])
    elif req["path"] == "/user-agent":
        ua = req["headers"].get("User-Agent", "")
        return reply(req, 200, ua)
    else:
        return reply(req, 404)

def parse_request(data):
    output = {"method": "", "path": "", "headers": {}, "body": ""}
    lines = data.decode("utf-8").split("\r\n")
    if len(lines) < 3:
        return None
    req_line = lines[0].split(" ")
    if req_line[0] not in ["GET", "POST", "PUT", "HEAD"]:
        return None
    output["method"] = req_line[0]
    output["path"] = req_line[1]

    lines = lines[1:]
    header_line_count = 0
    for line in lines:
        if line == "":
            break
        header_key, header_value = line.split(": ", 1)
        output["headers"][header_key] = header_value
        header_line_count += 1
    if len(lines) > header_line_count + 1:
        output["body"] = lines[header_line_count + 1]
    return output

def handle_client(conn):
    try:
        data = conn.recv(1024)
        if not data:
            return
        req = parse_request(data)
        if req is None:
            conn.send(b"HTTP/1.1 500 Internal Server Error\r\n\r\n")
        else:
            response = handle_request(req)
            conn.sendall(response)
    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        conn.close()

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("localhost", 4221))
    server_socket.listen()

    print("Server is listening on localhost:4221...")

    while True:
        conn, addr = server_socket.accept()
        print(f"Connected by {addr}")
        client_thread = Thread(target=handle_client, args=(conn,))
        client_thread.start()

if __name__ == "__main__":
    main()
