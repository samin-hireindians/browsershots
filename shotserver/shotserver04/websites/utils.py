# browsershots.org - Test your web design in different browsers
# Copyright (C) 2007 Johann C. Rocholl <johann@browsershots.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston,
# MA 02111-1307, USA.

"""
Utility functions for websites.
"""

__revision__ = "$Rev$"
__date__ = "$Date$"
__author__ = "$Author$"

import socket
import httplib
import urlparse

HTTP_TIMEOUT = 10 # seconds
MAX_RESPONSE_SIZE = 10000 # bytes


class HTTPError(Exception):
    """
    An error occurred while trying to load page content over HTTP.
    """

    def __init__(self, hostname, error=None):
        Exception.__init__(self)
        self.hostname = hostname
        if error is None:
            self.message = ''
        else:
            try:
                (error_code, error_string) = error.args
            except ValueError:
                error_string = str(error)
            self.message = error_string


class ConnectError(HTTPError):
    """Could not connect to remote HTTP server."""
    pass


class RequestError(HTTPError):
    """Could not send HTTP request to remote server."""
    pass


class ResponseError(HTTPError):
    """Could not read response from remote HTTP server."""
    pass


def split_netloc(netloc):
    """
    Split network locator into username, password, hostname, port.

    >>> split_netloc('example.com')
    (None, None, 'example.com', None)
    >>> split_netloc('user@example.com')
    ('user', None, 'example.com', None)
    >>> split_netloc('user:pw@example.com:80')
    ('user', 'pw', 'example.com', '80')
    """
    auth = username = password = None
    host = hostname = port = None
    if '@' in netloc:
        auth, host = netloc.split('@', 1)
    else:
        host = netloc
    if auth and ':' in auth:
        username, password = auth.split(':', 1)
    else:
        username = auth
    if host and ':' in host:
        hostname, port = host.split(':', 1)
    else:
        hostname = host
    return username, password, hostname, port


def http_get(url):
    """
    Try to download content from a remote HTTP server.

    >>> 'different browsers' in http_get('http://browsershots.org/')
    True
    >>> '404' in http_get('http://www.example.com/test.html')
    True
    """
    socket.setdefaulttimeout(HTTP_TIMEOUT)
    url_parts = urlparse.urlsplit(url)
    netloc_parts = split_netloc(url_parts[1])
    scheme = url_parts[0]
    hostname = netloc_parts[2]
    if netloc_parts[3] is not None:
        hostname += ':' + netloc_parts[3]
    try:
        if scheme == 'https':
            connection = httplib.HTTPSConnection(hostname)
        else:
            connection = httplib.HTTPConnection(hostname)
    except httplib.HTTPException, error:
        raise ConnectError(hostname, error)
    path = url_parts[2]
    if url_parts[3]:
        path += '?' + url_parts[3]
    try:
        return http_get_path(connection, path)
    finally:
        connection.close()


def http_get_path(connection, path):
    """
    Try to get content for this path through an existing connection.
    """
    # Send request
    try:
        headers = {"User-Agent": "Browsershots URL Check"}
        connection.request('GET', path, headers=headers)
    except socket.error, error:
        raise RequestError(connection.host, error)
    # Read response
    try:
        response = connection.getresponse()
        content = response.read(MAX_RESPONSE_SIZE)
        try:
            return content.decode('utf8')
        except UnicodeDecodeError:
            return content.decode('latin1')
    except socket.error, error:
        raise ResponseError(connection.host, error)


def count_profanities(profanities, content):
    """
    Count the number of profanities in page content.
    """
    result = 0
    content = content.lower()
    for word in profanities:
        result += content.count(word)
    return result


if __name__ == '__main__':
    import doctest
    doctest.testmod()