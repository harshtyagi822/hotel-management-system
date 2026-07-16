import multiprocessing

bind = "0.0.0.0:5000"

workers = multiprocessing.cpu_count() * 2 + 1
threads = 2
worker_class = "gthread"

timeout = 120
keepalive = 5

loglevel = "info"
accesslog = "-"
errorlog = "-"


