import logging

log = logging.getLogger("curricula")
log.propagate = False
log.setLevel(logging.INFO)

formatter = logging.Formatter(fmt="%(asctime)s %(levelname)s: %(message)s", datefmt="%m/%d/%y %I:%M:%S %p")
handler = logging.StreamHandler()
handler.setFormatter(formatter)
log.addHandler(handler)
