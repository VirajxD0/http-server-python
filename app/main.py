import socket
import os
import sys
from threading import Thread

def reply(req, code, body=b"", headers={}):
    b_reply = b""
    match code:
        case 200:
            b_reply += b"HTTP/1.1 200 OK\r\n"
        case 201:
            b_reply += b"HTTP/1.1 201 Created\r\n"
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
    
    b_reply += b"\r\n" + body  # Use body directly as bytes
    return b_reply

def handle_request(req, base_directory):
    if req["path"] == "/":
        return reply(req, 200)
    elif req["path"].startswith("/echo/"):
        return reply(req, 200, req["path"][6:].encode('utf-8'))
    elif req["path"].startswith("/files/"):
        filename = req["path"][7:]  # Get the filename from the path
        file_path = os.path.join(base_directory, filename)

        if req["method"] == "POST":
            # Read the body from the request
            body = req["body"]
            try:
                # Create a new file and write the body to it
                with open(file_path, 'wb') as f:
                    f.write(body)
                return reply(req, 201)  # Return 201 Created
            except Exception as e:
                print(f"Error writing file: {e}")
                return reply(req, 500)
        
        # Handle GET requests for existing files
        if os.path.isfile(file_path):
            with open(file_path, 'rb') as f:
                file_content = f.read()
            headers = {
                "Content-Type": "application/octet-stream",
                "Content-Length": str(len(file_content))
            }
            return reply(req, 200, file_content, headers)  # Send the file content as bytes
        else:
            return reply(req, 404)
    elif req["path"] == "/user-agent":
        ua = req["headers"].get("User-Agent", "")
        return reply(req, 200, ua.encode('utf-8'))
    else:
        return reply(req, 404)

def parse_request(data):
    output = {"method": "", "path": "", "headers": {}, "body": b""}
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

    # Read the body based on Content-Length
    content_length = int(output["headers"].get("Content-Length", 0))
    if len(lines) > header_line_count + 1:
        output["body"] = data.split(b"\r\n\r\n")[1][:content_length]  # Extract the body from the request data
    return output

def handle_client(conn, base_directory):
    try:
        data = conn.recv(1024)
        if not data:
            return
        req = parse_request(data)
        if req is None:
            conn.send(b"HTTP/1.1 500 Internal Server Error\r\n\r\n")
        else:
            response = handle_request(req, base_directory)
            conn.sendall(response)
    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        conn.close()

def main():
    # Default directory if not provided in testing
    base_directory = os.getcwd()  # Use current working directory as default

    if len(sys.argv) == 3 and sys.argv[1] == '--directory':
        base_directory = sys.argv[2]
    elif len(sys.argv) != 1:
        print("Usage: python your_program.py --directory <absolute_path>")
        return

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("localhost", 4221))
    server_socket.listen()

    print("Server is listening on localhost:4221...")

    while True:
        try:
            conn, addr = server_socket.accept()
            print(f"Connected by {addr}")
            client_thread = Thread(target=handle_client, args=(conn, base_directory))
            client_thread.start()
        except Exception as e:
            print(f"Error accepting connection: {e}")

if __name__ == "__main__":
    main()
