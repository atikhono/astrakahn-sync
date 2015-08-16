#!/usr/bin/env python3
'''
Derive integer types. Build synchroniser input term.
'''

from . import ast
from . import symtab
from . import exception as exn
from . import types


class CheckAST(ast.NodeVisitor):
    def __init__(self, i, o):
        self.intab = i
        self.outtab = o

    def visit_StoreType(self, node, _):
        intab = self.intab
        port = node.port
        if not intab.get(port.value):
            raise exn.NotDeclaredError("input channel '%s' not declared"
                    % port.value, port.coord)

    def visit_Trans(self, node, _):
        symtab = node.symtab
        intab = self.intab
        port = node.port
        cond = node.condition

        ce = CheckExp(symtab)
        ce.traverse(node)

        port_ent = intab.get(port.value)
        if not port_ent:
            raise exn.NotDeclaredError("input channel '%s' not declared"
                    % port.value, port.coord)

        # Build input term for port
        if isinstance(cond, ast.CondDataMsg):
            if not cond.labels and not cond.tail.value:
                rec = types.Record(labels={}, tails=[types.Variable()])
            else:
                rec = types.Record(labels={}, tails=[])

            for l in cond.labels:
                l_ent = symtab.get(l.value)
                rec.merge(types.Record(labels={l.value:l_ent.type}, tails=[]))

            tail = cond.tail
            if tail.value:
                tail_ent = symtab.get(tail.value)
                if isinstance(tail_ent.type, types.Number):
                    rec.merge(types.Record(labels={tail.value:tail_ent.type}, tails=[]))
                if isinstance(tail_ent.type, types.Record):
                    rec.merge(tail_ent.type)
                if isinstance(tail_ent.type, types.Variable):
                    rec.merge(types.Record(labels={}, tails=[tail_ent.type]))


            choice = cond.choice
            if choice.value:
                l = choice.value
            else:
                l = 'uniq'

            ch = types.Choice(variants={l:rec}, tails=[])
            port_ent.type.merge(ch)
            # Fix port type tail when there are several transitions
            # on port %p. Port type always has the only tail.
            #   p.(x, y || t)
            #   p.(z || h)
            # #=> p.type.variants['uniq'] = { x, y, z | j }
            #     t.type = { z | j }
            #     h.type = { x, y | j }
            # Tail types (t, h) are calculated in outtab.py.
            # After that THIS.type is updated. THIS.type is the same for all
            # transitions on port %p.
            port_tails = port_ent.type.variants[l].tails
            if len(port_tails) > 1:
                port_ent.type.variants[l].tails = [types.Variable()]

    def visit_Send(self, node, _):
        outtab = self.outtab
        port = node.port
        if not self.outtab.get(port.value):
            raise exn.NotDeclaredError("output channel '%s' not declared"
                    % port.value, port.coord)

    #--------------------------------------------------
    def generic_visit(self, node, children):
        return None


class CheckExp(ast.NodeVisitor):
    def __init__(self, s):
        self.symtab = s

    def visit_Assign(self, node, _):
        dest = node.lhs
        exp = node.rhs
        symtab = self.symtab
        dest_ent = symtab.get(dest.value)
        if not dest_ent:
            raise exn.NotDeclaredError("variable '%s' not declared"
                    % dest.value, dest.coord)
        if dest_ent.readonly:
            raise exn.NotAssignableError("cannot assign to variable '%s' declared"
                    % dest.value, dest.coord, dest_ent.ast.coord)

        if isinstance(dest_ent.type, types.Number):
            if not isinstance(exp, ast.IntExp):
                raise exn.TypeError("Type mismatch as data expression "
                        "assigned to variable '%s' declared integer"
                        % dest.value, dest.coord, dest_ent.ast.coord)
        else:
            if not isinstance(exp, ast.DataExp):
                raise exn.TypeError("Type mismatch as integer expression "
                        "assigned to variable '%s' declared data"
                        % dest.value, dest.coord, dest_ent.ast.coord)

    def visit_IntExp(self, node, _):
        symtab = self.symtab
        terms = node.terms
        for arg_ast in [terms[t] for t in terms if isinstance(terms[t], ast.ID)]:
            arg = arg_ast.value
            arg_ent = symtab.get(arg)
            if arg_ent is None:
                raise exn.NotDeclaredError("variable '%s' not declared"
                        % arg, arg_ast.coord)

            if arg_ent.readonly and isinstance(arg_ent.type, types.Variable):
                arg_ent.type = types.Int()

            if not isinstance(arg_ent.type, types.Number):
                    raise exn.TypeError("Type mismatch as variable '%s' found "
                            "in integer expression declared data"
                            % arg, arg_ast.coord, arg_ent.ast.coord)

    def visit_DataExp(self, node, _):
        symtab = self.symtab
        for item in node.items:
            if isinstance(item, ast.ItemVar):
                item_ent = symtab.get(item.name.value)
                if item_ent is None:
                    raise exn.NotDeclaredError("variable '%s' not declared"
                            % item.name.value, item.name.coord)

                if isinstance(item_ent.type, types.Variable):
                    item_ent.type = types.Record(labels={}, tails=[types.Variable()])

                if isinstance(item_ent.type, types.Number):
                    raise exn.TypeError("Type mismatch as variable '%s' "
                            "found in data expression declared integer"
                            % item.name.value, item.name.coord, item_ent.ast.coord)
            if isinstance(item, ast.ItemExpand):
                item_ent = symtab.get(item.name.value)
                if item_ent is None:
                    raise exn.NotDeclaredError("variable '%s' not declared"
                            % item.name.value, item.name.coord)

    #--------------------------------------------------
    def generic_visit(self, node, children):
        return None


def build(sync_ast):
    intab = sync_ast.inputs.symtab
    outtab = sync_ast.outputs.symtab

    ca = CheckAST(intab, outtab)
    ca.traverse(sync_ast)
