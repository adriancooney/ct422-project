from container import Container

class Question(Container):
    def __init__(self, index):
        Container.__init__(self)
        self.index = index
        
    def __repr__(self):
        return "Question[%s, questions=%d]" % (self.index, len(self.contents))