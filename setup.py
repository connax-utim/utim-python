import setuptools
from utim import __version__

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="utim",
    version=__version__,
    license='Apache 2.0',
    author="Connax OY",
    author_email="info@connax.io",
    description="Open source version of Universal Thing Identity Module (UTIM) for IoT devices",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/connax-utim/utim-python",
    packages=setuptools.find_packages(exclude=['examples']),
    platforms='any',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'paho-mqtt',
        'pika',
        'six',
        'pycrypto',
    ],
)
