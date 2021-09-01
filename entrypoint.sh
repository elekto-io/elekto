#!/usr/bin/env bash
set -e 

echo "updating the $DB_CONNECTION database"
./console --migrate

echo "syncing repo $META_REPO"
./console --sync

echo "starting Elekto"
if [ "$APP_DEBUG" == "True" ]; then
  echo "in Debug mode"
  ./console --run
else
  if [ $APP_CONNECT == "socket" ]; then
    # socket mode for fronting by nginx
    echo "with a socket connection on $APP_PORT"
    uwsgi --module elekto:APP --processes 8 --socket :$APP_PORT
  else
    # http mode for direct connection
    echo "with an http connection on $APP_PORT"
    uwsgi --module elekto:APP --processes 8 --http :$APP_PORT
  fi
fi
