#!/bin/bash
cd backend
gunicorn --bind=0.0.0.0:8000 --timeout 600 app:app