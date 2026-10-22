#!/bin/sh

python -m gunicorn logviewer2.web:app --preload --workers 3 --access-logfile -