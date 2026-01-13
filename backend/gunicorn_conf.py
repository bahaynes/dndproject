import os
import multiprocessing

# Gunicorn configuration file
# https://docs.gunicorn.org/en/stable/configure.html#configuration-file

# The socket to bind
# Render sets the PORT environment variable
port = os.getenv("PORT", "10000")
bind = f"0.0.0.0:{port}"

# Worker Options
# Workers are the number of processes to run
# For production, it is recommended to use (2 x num_cores) + 1
# For free tier (low cpu), 1-2 workers is usually enough.
workers = 2
# workers = multiprocessing.cpu_count() * 2 + 1

# Worker class
# Use uvicorn workers for FastAPI
worker_class = "uvicorn.workers.UvicornWorker"

# Logging
loglevel = "info"
accesslog = "-"  # stdout
errorlog = "-"   # stderr

# Keepalive (important for load balancers)
keepalive = 120
