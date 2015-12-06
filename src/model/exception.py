class ModelException(Exception):
    def __init__(self, type, message):
        self.type = type
        self.message = message

class NotFound(ModelException):
    def __init__(self, type, message):
        ModelException.__init__(self, type, message)

class InvalidInput(ModelException):
    def __init__(self, type, message):
        ModelException.__init__(self, type, message)