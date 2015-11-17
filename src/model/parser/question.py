from container import Container

class Question(Container):
    def __init__(self, index):
        Container.__init__(self)
        self.index = index
        self.text = None

    def setText(self, text):
        self.text = text
        
    def __repr__(self):
        return "Question[%s, questions=%d]" % (self.index, len(self.contents))
