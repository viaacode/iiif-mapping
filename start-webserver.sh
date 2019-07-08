#!/bin/bash
cd `dirname "$0"`

echo Starting Gunicorn.
gunicorn app:app --bind 0.0.0.0:8080 --preload --workers 4
