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


class DuplicatesError(Exception):
    '''
    Symtab duplicate symbol exception.
    '''
    def __init__(self, msg, coord, coord_dup):
        self.msg = msg
        self.coord = coord
        self.coord_dup = coord_dup

    def message(self, code):
        '''
        Return the error message with the positional information.
        The message comes in the form:

            "lineno:linepos: message at lineno_dup:linepos_dup"

        linepos and linepos_dup are relative to %code%.
        '''
        return "%s: %s at %s" % (self.coord.linepos(code), self.msg,
                self.coord_dup.linepos(code))


class NotDeclaredError(ParseError): pass
class NotAssignableError(DuplicatesError): pass
class TypeError(DuplicatesError): pass

class NotImplemented(Exception): pass
