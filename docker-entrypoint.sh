#!/bin/sh
# Runs on container start. Applies any pending Alembic migrations, then hands
# off (exec) to whatever command was passed - normally the uvicorn CMD.
#
# `set -e` : abort if a command fails, so a broken migration stops startup
#            instead of launching the app against an out-of-date schema.
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting application..."
# exec replaces this shell with the app process, so it becomes PID 1 and
# receives Docker's stop signals directly (clean shutdowns).
exec "$@"