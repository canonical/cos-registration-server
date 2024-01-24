#!/usr/bin/bash

mkdir ~/server_data

SECRET_KEY=$(/bin/python3 -c \
'from django.core.management.utils import get_random_secret_key;
print(get_random_secret_key())')
echo $SECRET_KEY > ~/server_data/secret_key
