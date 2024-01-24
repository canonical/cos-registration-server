#!/usr/bin/bash

# necessary for daphne as the option --root-path doesn't work
cd /lib/python3.10/site-packages/cos_registration_server

export DATABASE_BASE_DIR_DJANGO="/server_data"
export SECRET_KEY_DJANGO=$(cat /server_data/secret_key)

python manage.py createsuperuser
