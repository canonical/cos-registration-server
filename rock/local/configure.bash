#!/usr/bin/bash

cd /lib/python3.10/site-packages/cos_registration_server

export DATABASE_BASE_DIR_DJANGO="/server_data"
export SECRET_KEY_DJANGO=$(cat /server_data/secret_key)

# migrate the database
/bin/python3 manage.py migrate

# update all the dashboards
python3 manage.py update_all_dashboards
