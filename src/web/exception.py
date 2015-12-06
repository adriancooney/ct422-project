class HttpException(Exception):
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message

class MissingParameter(HttpException):
    def __init__(self, name, type="POST"):
        HttpException.__init__(400, "Missing %s parameter %s." % (type, name))
