class InvalidStringError(Exception):
    """the string did not match any allowed patterns"""
    def __init__(self, string, valid_choices, multiple_hits=False):
        super().__init__()
        
        self.string = string
        self.valid_choices = valid_choices
        self.multiple_hits = multiple_hits

    def __str__(self):
        if self.multiple_hits:
            attr = 'does not uniquely match one'
        else:
            attr = 'matches none'
        return "The string \'{0!s}\' {1!s} of the options: {2!r}".format(self.string,attr,self.valid_choices)
        
def validatestring(s,valid_choices):
    hits = [item.startswith(s) for item in valid_choices]
    nhits = hits.count(True)
    if nhits != 1:
        raise InvalidStringError(s,valid_choices,nhits>1)
    return valid_choices[hits.index(True)]

if __name__ == '__main__':
    None