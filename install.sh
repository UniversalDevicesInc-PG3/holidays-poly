#!/usr/bin/env sh

pip3 install -r requirements.txt --user
python3 -m unittest discover tests
