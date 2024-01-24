#!/usr/bin/bash

cd /lib/python3.10/site-packages/cos_registration_server

export DATABASE_BASE_DIR_DJANGO="~/server_data"

# migrate the database
/bin/python3 manage.py migrate
