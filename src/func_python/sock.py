import ipaddress
import logging
import os
import socket


DEFAULT_LISTEN_ADDRESS = '[::]:8080,0.0.0.0:8080'

def bind() -> list[str]:
    """
    This function reads the 'LISTEN_ADDRESS' environment variable and binds sockets according to it's content.
    This function gives us some more control over how sockets are created.
    We creat them ourselves here, and forward them in the "fd://{fd}" format to the hypercorn server.
    :return: Sequence of "bind" strings in format expected by the hypercorn server config.
    """

    listen_addresses = os.getenv('LISTEN_ADDRESS', DEFAULT_LISTEN_ADDRESS).split(",")

    fixup_ipv4_unspecified(listen_addresses)

    ipv4_only = not socket.has_dualstack_ipv6()
    result: list[str] = []

    for address in listen_addresses:
        if address.startswith("unix://") or address.startswith("fd://"):
            logging.error(f'unsupported schema: <{address}>')
            continue
        sock: socket.socket

        [host, port] = address.rsplit(":", 1)
        if '[' in host:
            if ipv4_only:
                logging.warning(f'not binding <{address}> since IPv6 is not available')
                continue
            host = host.strip('[]')
            sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            try:
                sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
            except socket.error as e:
                logging.warning(f"cannot set IPV6_V6ONLY: {e}")
        else:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            sock.bind((host, int(port)))
            result.append(f'fd://{sock.detach()}')
        except socket.error as e:
            logging.error(f"cannot bind socket <{address}>: {e}")

    if len(result) <= 0:
        raise Exception('failed to bind any sockets')

    return result

def fixup_ipv4_unspecified(listen_addresses: list[str]) -> None:
    """
    This function checks if the listen addresses contains unspecified IPv6 address but not unspecified IPv4 address.
    If that's the case the function will insert appropriate unspecified IPv4 address into the list.
    """
    ipv6_unspecified_port = None
    ipv4_unspecified = False
    for la in listen_addresses:
        if la.startswith("unix://") or la.startswith("fd://"):
            continue
        [host,port] = la.rsplit(":", 1)
        ip = ipaddress.ip_address(host.strip('[]'))
        if ip.is_unspecified:
            if isinstance(ip, ipaddress.IPv6Address):
                ipv6_unspecified_port = port
            if isinstance(ip, ipaddress.IPv4Address):
                ipv4_unspecified = True
    if ipv6_unspecified_port is not None and not ipv4_unspecified:
        listen_addresses.append('0.0.0.0:' + ipv6_unspecified_port)
