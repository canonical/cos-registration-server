#!/usr/bin/bash

cd /lib/python3.10/site-packages/cos_registration_server

export DATABASE_BASE_DIR_DJANGO="/server_data"
export SECRET_KEY_DJANGO=$(cat /server_data/secret_key)

gunicorn --bind 0.0.0.0:8000 cos_registration_server.wsgi
