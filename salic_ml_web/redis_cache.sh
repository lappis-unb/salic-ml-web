#!/usr/bin/env bash
echo "Attempting to preload indicators into Redis"
python3 /salic_ml_web/manage.py shell < /salic_ml_web/redis_cache.py
