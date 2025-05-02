class SessionException(Exception):
    def __init__(self, message):
        self.stderr = message
