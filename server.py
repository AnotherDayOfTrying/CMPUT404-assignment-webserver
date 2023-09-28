#  coding: utf-8 
import socketserver

# Copyright 2023 Abram Hindle, Eddie Antonio Santos, Justin Javier
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# Furthermore it is derived from the Python documentation examples thus
# some of the code is Copyright © 2001-2013 Python Software
# Foundation; All Rights Reserved
#
# http://docs.python.org/2/library/socketserver.html
#
# run: python freetests.py

# try: curl -v -X GET http://127.0.0.1:8080/


# request -> base_handler -> handler

class MyWebServer(socketserver.BaseRequestHandler):
    __SERVE_DIRECTORY = "www"
    __EXTENSION_TO_MIME = {"css": "text/css", "html": "text/html"}

    def handle(self):
        response = b''
        try:
            request = self.request.recv(1024).strip()
            if len(request) == 0: # client terminated connection
                return
            method, resource, header = self.parse_request(str(request, "utf-8"))
            print(method, resource, header)
            if method != "GET":
                response = self.respond_405_Method_Not_Allowed()
                return
            if not (self.has_trailing_slash(resource) or self.has_file_extension(resource)):
                response = self.respond_301_Moved_Permanently(resource)
                return
            response = self.respond_200_OK(resource)
        except FileNotFoundError as exception:
            response = self.respond_404_Not_Found(exception.filename)
        except Exception as exception: # 5xx here
            response = self.respond_500_Internal_Server_Error()
            raise exception # base class handles any escalated exceptions
        finally:
            self.request.sendall(response)
    
    def respond_200_OK(self, resource):
        file, extension = self.read_file(resource)
        return bytearray(f"HTTP/1.1 200 OK\nContent-Type:{MyWebServer.__EXTENSION_TO_MIME[extension]}\n\n{file}\n", "utf-8")
    
    def respond_301_Moved_Permanently(self, resource):
        return bytearray(f"HTTP/1.1 301 Moved Permanently\nLocation:{resource}/\n", "utf-8")
    
    def respond_404_Not_Found(self, exception):
        body = f"<html><h1>404 Not Found</h1><p>Cannot find {exception}</p></html>"
        return bytearray(f"HTTP/1.1 404 Not Found\n\n{body}\n", "utf-8")

    def respond_405_Method_Not_Allowed(self):
        return bytearray("HTTP/1.1 405 Method Not Allowed\n", "utf-8")
    
    def respond_500_Internal_Server_Error(self):
        return bytearray(f"HTTP/1.1 500 Internal Server Error", "utf-8")
    
    def parse_request(self, req: str) -> (str, str):
        lines = req.split('\n')
        request_line = lines.pop(0)
        method, resource, _ = request_line.split(' ')
        is_body = False
        headers = {}
        body = []
        for line in lines:
            stripped_line = line.strip()
            if len(stripped_line) == 0:
                is_body = True
            if is_body is True:
                body.append(line)
            else:
                headers[line.split(':')[0].strip()]: line.split(':')[1].strip()
        return method, resource, headers
    
    def read_file(self, resource):
        read_file = ""
        if resource[-1] == "/":
            resource += "index.html"
        extension = resource.split('.')[1]
        with open(f"./{self.__SERVE_DIRECTORY}/{resource}", "r") as file:
            read_file += file.read()
        return read_file, extension
    
    def has_file_extension(self, resource):
        return resource.rfind('.') > resource.rfind('/')

    def has_trailing_slash(self, resource):
        return resource[-1] == "/"

if __name__ == "__main__":
    HOST, PORT = "localhost", 8080

    socketserver.TCPServer.allow_reuse_address = True
    # Create the server, binding to localhost on port 8080
    server = socketserver.TCPServer((HOST, PORT), MyWebServer)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
