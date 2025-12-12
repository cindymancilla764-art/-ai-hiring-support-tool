import datetime

def log_event(event_type, details):
    print(f"{datetime.datetime.now()} — {event_type}: {details}")
