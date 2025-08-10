#!/bin/bash

echo "Initializing DB..."
python3 db/loader.py

echo "Starting Flask app..."
export FLASK_APP=app.py
export FLASK_ENV=development
flask run
