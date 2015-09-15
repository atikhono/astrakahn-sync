class ParseError(Exception):
    '''
    Parsing exception.
    '''
    def __init__(self, msg, coord=None):
        self.msg = msg
        self.coord = coord

    def message(self, code):
        '''
        Return the error message with the positional information.
        The message comes in the form:

            "lineno:linepos: message" if the line number %lineno% and the lexing
            position %lexpos% where the error occured are known;

            "EOF: message" end of file/otherwise.

        The function calculates the line position %linepos% of the error in
        %code%.
        '''
        if self.coord is None:
            return "EOF: %s" % self.msg
        else:
            return "%s: %s" % (self.coord.linepos(code), self.msg)


class NotImplemented(Exception): pass