class Coord(object):
    '''
    Wrap symbol positional information as provided by PLY into an object.

    Attributes:
        lineno (int): line number where the symbol is found in the source
        code.
        lexpos (int): lexing position where the symbol is found in the
        source code.
    '''
    def __init__(self, lineno, lexpos):
        self.lineno = lineno
        self.lexpos = lexpos

    def linepos(self, code):
        '''
        Return the positional information in the form

            %line number% : %position in line%

        relative to %code%.
        '''
        lineno = self.lineno
        lexpos = self.lexpos
        last_cr = code.rfind('\n', 0, lexpos)
        if last_cr < 0:
            linepos = lexpos + 1
        else:
            linepos = lexpos - last_cr
        return "%s:%s" % (lineno, linepos)

    def show(self):
        '''
        Print the positional information as is.
        '''
        return "%s:%s" % (self.lineno, self.lexpos)
