#!/bin/sh

poetry run python -m gunicorn logviewer2.web:app -c gunicorn.conf.py