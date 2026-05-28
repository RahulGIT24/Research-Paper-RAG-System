class BaseAPIException(Exception):
    def __init__(self, status_code,message):
        self.statuscode = status_code
        self.message = message