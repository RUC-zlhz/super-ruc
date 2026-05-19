#!/usr/bin/env python3
"""Minimal HTTP proxy that forwards through an upstream SOCKS5 proxy.

This is intended for server-local build traffic only. It listens on
127.0.0.1:18081 by default and forwards outbound requests via the SSH
reverse SOCKS endpoint at 127.0.0.1:18080.
"""
from __future__ import annotations

import http.client
import select
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

UPSTREAM_SOCKS_HOST = "127.0.0.1"
UPSTREAM_SOCKS_PORT = 18080
LISTEN_HOST = "127.0.0.1"
LISTEN_PORT = 18081


def socks_connect(target_host: str, target_port: int) -> socket.socket:
    sock = socket.create_connection((UPSTREAM_SOCKS_HOST, UPSTREAM_SOCKS_PORT), timeout=20)
    sock.settimeout(20)

    sock.sendall(b"\x05\x01\x00")
    method = sock.recv(2)
    if len(method) != 2 or method[0] != 0x05 or method[1] != 0x00:
        raise RuntimeError("SOCKS5 auth negotiation failed")

    try:
        addr = socket.inet_pton(socket.AF_INET, target_host)
        atyp = b"\x01"
    except OSError:
        try:
            addr = socket.inet_pton(socket.AF_INET6, target_host)
            atyp = b"\x04"
        except OSError:
            encoded = target_host.encode("idna")
            if len(encoded) > 255:
                raise ValueError("hostname too long for SOCKS5")
            atyp = b"\x03" + bytes([len(encoded)])
            addr = encoded
    port_bytes = target_port.to_bytes(2, "big")
    request = b"\x05\x01\x00" + atyp + addr + port_bytes
    sock.sendall(request)

    header = sock.recv(4)
    if len(header) != 4 or header[0] != 0x05:
        raise RuntimeError("SOCKS5 connect response malformed")
    if header[1] != 0x00:
        raise RuntimeError(f"SOCKS5 connect failed with code {header[1]}")

    atyp_resp = header[3]
    if atyp_resp == 0x01:
        sock.recv(4)
    elif atyp_resp == 0x04:
        sock.recv(16)
    elif atyp_resp == 0x03:
        length = sock.recv(1)[0]
        sock.recv(length)
    else:
        raise RuntimeError("SOCKS5 response addr type unsupported")
    sock.recv(2)
    return sock


class ProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return

    def _target(self) -> tuple[str, int, str]:
        if self.path.startswith(("http://", "https://")):
            parsed = urlsplit(self.path)
            host = parsed.hostname or self.headers.get("Host", "")
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            path = parsed.path or "/"
            if parsed.query:
                path += "?" + parsed.query
            return host, port, path

        host_header = self.headers.get("Host", "")
        if ":" in host_header:
            host, port_text = host_header.rsplit(":", 1)
            port = int(port_text)
        else:
            host = host_header
            port = 80
        return host, port, self.path or "/"

    def do_CONNECT(self) -> None:  # noqa: N802
        host, port_text = self.path.split(":", 1)
        port = int(port_text)
        upstream = socks_connect(host, port)
        self.connection.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        try:
            while True:
                ready, _, _ = select.select([self.connection, upstream], [], [])
                if self.connection in ready:
                    data = self.connection.recv(65536)
                    if not data:
                        break
                    upstream.sendall(data)
                if upstream in ready:
                    data = upstream.recv(65536)
                    if not data:
                        break
                    self.connection.sendall(data)
        finally:
            upstream.close()

    def _proxy_http(self) -> None:
        host, port, path = self._target()
        upstream = socks_connect(host, port)
        try:
            request_lines = [f"{self.command} {path} {self.request_version}\r\n"]
            for key, value in self.headers.items():
                if key.lower() in {"proxy-connection", "proxy-authorization", "connection"}:
                    continue
                request_lines.append(f"{key}: {value}\r\n")
            request_lines.append("Connection: close\r\n\r\n")
            upstream.sendall("".join(request_lines).encode("latin-1"))
            if self.command in {"POST", "PUT", "PATCH"}:
                content_length = int(self.headers.get("Content-Length", "0") or "0")
                remaining = content_length
                while remaining > 0:
                    chunk = self.rfile.read(min(65536, remaining))
                    if not chunk:
                        break
                    upstream.sendall(chunk)
                    remaining -= len(chunk)

            response = http.client.HTTPResponse(upstream)
            response.begin()
            self.send_response(response.status, response.reason)
            for header, value in response.headers.items():
                if header.lower() == "transfer-encoding" and value.lower() == "chunked":
                    continue
                if header.lower() == "connection":
                    continue
                self.send_header(header, value)
            self.end_headers()
            while True:
                chunk = response.read(65536)
                if not chunk:
                    break
                self.wfile.write(chunk)
        finally:
            upstream.close()

    def do_GET(self) -> None:  # noqa: N802
        self._proxy_http()

    def do_POST(self) -> None:  # noqa: N802
        self._proxy_http()

    def do_PUT(self) -> None:  # noqa: N802
        self._proxy_http()

    def do_PATCH(self) -> None:  # noqa: N802
        self._proxy_http()

    def do_DELETE(self) -> None:  # noqa: N802
        self._proxy_http()


def main() -> None:
    server = ThreadingHTTPServer((LISTEN_HOST, LISTEN_PORT), ProxyHandler)
    print(f"HTTP proxy listening on http://{LISTEN_HOST}:{LISTEN_PORT}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
