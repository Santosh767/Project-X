#!/bin/bash
# Start Celery worker and beat scheduler

echo "Starting Celery worker..."
celery -A celery_worker.celery worker --loglevel=info --pool=solo &

echo "Starting Celery beat scheduler..."
celery -A celery_worker.celery beat --loglevel=info &

echo "Celery started!"