#!/bin/bash

# Log script start
echo "Starting setup script."

# Configure script to exit when any command fails
set -e

# Monitor last executed command
trap 'last_command=$current_command; current_command=$BASH_COMMAND' DEBUG

# Log error message upon script exit
trap '[ $? -eq 1 ] && echo "Backend failed."' EXIT

# Parse command line arguments
migrate=false
load_fixtures=false
sync_views=false
run_server=false
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --migrate) migrate=true; shift ;;
        --load-fixtures) load_fixtures=true; shift ;;
        --sync-views) sync_views=true; shift ;;
        --run-server) run_server=true; shift ;;
        *) echo "Unknown command line parameter received: $1"; exit 1 ;;
    esac
done

# Perform model migrations if indicated 
# (WARNING: Defaults to "yes" for all questions)
if $migrate ; then
    echo "Creating database migrations from Django models."
    yes | ./manage.py makemigrations

    echo "Applying migrations to database."
    yes | ./manage.py migrate
fi

# Load fixtures if indicated 
if $load_fixtures ; then
    echo "Loading fixtures into database tables."
    ./manage.py loaddata edgar_place_codes
fi

# Sync views if indicated
if $sync_views ; then
    echo "Syncing database views from Django models."
    ./manage.py sync_pgviews --force
fi

# Log successful end of database setup
echo "Database setup completed successfully."

# Run development server if indicated
if $run_server ; then
    echo "Running default development server."
    ./manage.py runserver 0.0.0.0:8080
fi