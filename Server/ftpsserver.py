import os

from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import TLS_FTPHandler
from pyftpdlib.servers import FTPServer

#Include Certificate for TLS Encryption
CERTFILE = os.path.abspath(os.path.join(os.path.dirname(__file__),"sec/keycert.pem"))


def main():
    # Instantiate a dummy authorizer for managing 'virtual' users
    authorizer = DummyAuthorizer()
    # Define a new user having full r/w permissions
    authorizer.add_user('user', '12345', '.', perm='elradfmwMT')
    # Instantiate TLS_FTP handler class
    handler = TLS_FTPHandler
    handler.certfile = CERTFILE
    handler.authorizer = authorizer
    # Requires SSL for both control and data channel
    handler.tls_control_required = True
    handler.tls_data_required = True
    # Start server
    server = FTPServer(('', 2121), handler)
    server.serve_forever()


if __name__ == '__main__':
    main()
