"""Simple function to check if internet connection is available.

Shamelessly copied from:
http://stackoverflow.com/a/33117579/3087339
"""
import socket

def internet_is_connected(host="8.8.8.8", port=53, timeout=5):
    """"
    Host: 8.8.8.8 (google-public-dns-a.google.com)
    OpenPort: 53/tcp
    Service: domain (DNS/TCP)
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception as ex:
        return False
