#
# This class is used for storing channel ids/types as well.
# Probably it's not ok because:
#   - Channel table's never a tree, so tree functionality
#     is redundant for it,
#   - Channel table entry doesn't need 'readonly' attribute
#     (may introduce a separate class for channel table
#     entries in future).
#
# FIXME All show functions should write to buffer similar to
#       ast.show()
#
class Symtab(object):
    '''
    Implements chained symbol table.

    Attributes:
        table (dict of str:<Entry>): a symbol table iteself.
        prev (<Symtab>): points to the previous symtab in the chain.

    Potentially this structure forms a tree of symbol tables.
    prev = None indicates the root of the tree.
    '''
    def __init__(self, p):
        self.table = {}
        self.prev = p

    def put(self, sym_id, sym_entry):
        '''
        Put a key-value pair %sym_id% : %sym_entry% in the table.
        '''
        t = self.get(sym_id)
        if t is None:
            self.table[sym_id] = sym_entry
        return t

    def get(self, sym_id):
        '''
        Find an entry for %sym_id% in the chain of tables.
        '''
        symtab = self
        while symtab is not None:
            found = symtab.table.get(sym_id)
            if found is not None:
                return found
            else:
                symtab = symtab.prev
        return None

    def show(self):
        '''
        Print the symtab.
        '''
        symtab = self
        while symtab is not None:
            for sym_id in symtab.table:
                entry = symtab.table[sym_id]
                print("'%s': type = %s, ro = %s, ast = "
                        % (sym_id, entry.type.show(), entry.readonly), end='')
                entry.ast.show()
            symtab = symtab.prev


class Entry(object):
    '''
    Implements a symbol table entry.

    Attributes:
        type (<type.Type>): stores the CAL type of the symbol
        ast (<ast.Ast>): stores the AST of the symbol
        readonly (bool): indicates a read-only value, e g pattern-matched values
        and enum range values are assigned just once.
    '''
    def __init__(self, type, ast, ro=False):
        self.type = type
        self.ast = ast
        self.readonly = ro
