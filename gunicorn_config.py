"""
Gunicorn configuration file for Aristotle WhatsApp bot.
"""

import os
import multiprocessing

# Server socket
bind = os.environ.get('GUNICORN_BIND', '0.0.0.0:8001')

# Worker processes
workers = int(os.environ.get('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = 'sync'
worker_connections = 1000
timeout = 120
keepalive = 2

# Process naming
proc_name = 'aristotle-whatsapp'

# Logging
accesslog = 'logs/access.log'
errorlog = 'logs/error.log'
loglevel = 'info'

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# SSL
forwarded_allow_ips = '*'
secure_scheme_headers = {'X-Forwarded-Proto': 'https'}

#gunicorn --config gunicorn_config.py app:app