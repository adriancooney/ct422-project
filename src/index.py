class Index:
    def __init__(self, index_type, value):
        self.index_type = index_type
        self.value = value
        self.i = int()
    
    def is_next(self, index):
        """Returns whether an index passed is of the same type
        and i + 1
        
        e.g.
            Index("alpha", "a").isNext(Index("alpha", "b")) # true
            Index("numerical", "1").isNext(Index("roman", "ii")) # false
        """
        return index.index_type == self.index_type and (index.i - self.i) == 1 
    
    roman = { 'i': 1, 'v': 5, 'x': 10 }

    def __int__(self):
        if self.index_type is "alpha":
            return pp.alphas.index(self.value.lower())
        elif self.index_type is "roman":
            numerals = self.value.lower()
            total = 0
            for special in ('iv', 'ix'):
                if numerals.count(special):
                    total += (Index.roman[special[1]] - 1) * numerals.count(special)
                    numerals = numerals.replace(special, '')
            return total + sum(Index.roman[n] for n in numerals)
        else:
            return self.value
        
    def __str__(self):
        return "Index[type=%s, value=%s, i=%d]" % (self.index_type, self.value, self.i)
    
    def __repr__(self):
        return str(self)