[![License badge](https://img.shields.io/badge/license-Apache2-orange.svg)](http://www.apache.org/licenses/LICENSE-2.0) [![Documentation Status](https://readthedocs.org/projects/utim/badge/?version=latest)](https://utim.readthedocs.io/en/latest/?badge=latest)

# utim-python
Open source version of Universal Thing Identity Module (UTIM) for IoT devices written on Python 

## Installation

Use `pip` for python3:

    pip3 install --extra-index-url https://test.pypi.org/simple/ utim

## Launch

Example of Utim launcher is in `examples` folder

Before you run launcher you need:

1. Run Uhost [https://github.com/connax-utim/uhost-python]

1. Set environment variable `UTIM_MASTER_KEY`. Value of this variable is in hex format. For example:

        UTIM_MASTER_KEY=6b6579       

1. Edit `config.ini` file (in the same folder), or create config file in the other place and set environment variable `UTIM_CONFIG`. Value of this variable is a absolute path to `config.ini`.