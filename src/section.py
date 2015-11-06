from question import Question

class Section(Container):
    def __repr__(self):
        return "Section[%s, questions=%d]" % (self.index, len(self.questions))