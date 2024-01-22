#!/usr/bin/bash

# necessary for daphne as the option --root-path doesn't work
cd $SNAP/lib/python3.10/site-packages/cos_registration_server

export DATABASE_BASE_DIR_DJANGO=$SNAP_COMMON
export SECRET_KEY_DJANGO=$(snapctl get secret-key)

$SNAP/bin/daphne cos_registration_server.asgi:application
