#!/usr/bin/env python3
'''
Derive store types. Build synchroniser output term.
'''

from . import ast
from . import symtab
from . import exception as exn
from . import types


class CheckAST(ast.NodeVisitor):
    def __init__(self, i, o):
        self.intab = i
        self.outtab = o

    def visit_Trans(self, node, _):
        symtab = node.symtab
        intab = self.intab
        outtab = self.outtab
        port = node.port
        cond = node.condition

        # Update THIS.tail.type and THIS.type from intab
        #   p.(x, y || t)
        #   p.(x, y, z || h)
        # #=> t.type = { z | j }
        #     h.type = { | j }
        #     intab[p].variants['uniq'] = { x, y, z || j }
        this_ent = symtab.get('this')
        port_ent = intab.get(port.value)

        if isinstance(cond, ast.CondDataMsg):
            choice = cond.choice
            if choice.value:
                c = choice.value
            else:
                c = ['uniq']
            var_rec = port_ent.type.variants[c]

            # Calculate tail type
            tail_rec = types.Record(labels={}, tails=[])
            cond_labels = [l.value for l in cond.labels]
            for l in var_rec.labels:
                if l not in cond_labels:
                    tail_rec.merge(types.Record(labels={l:var_rec.labels[l]}, tails=[]))
            tail_rec.tails = var_rec.tails

            # Update tail type
            tail = cond.tail
            if tail.value:
                tail_ent = symtab.get(tail.value)
                tail_ent.type = tail_rec

            # Update THIS.type
            this_ent.type = var_rec
        else:
            this_ent.type = port_ent.type.variants['uniq']

        cde = CheckDataExp(symtab, outtab)
        cde.traverse(node)

    #--------------------------------------------------
    def generic_visit(self, node, children):
        return None


def get_dataexp_type(exp, symtab):
    rec = types.Record(labels={}, tails=[])
    for item in exp.items:
        if isinstance(item, ast.ItemVar):
            item_ent = symtab.get(item.name.value)
            rec.merge(item_ent.type)
        if isinstance(item, ast.ItemExpand):
            item_ent = symtab.get(item.name.value)
            rec.merge(types.Record(labels={item.name.value:item_ent.type}, tails=[]))
        if isinstance(item, ast.ItemPair):
            rec.merge(types.Record(labels={item.label.value:types.Int()}, tails=[]))
        if isinstance(item, ast.ItemThis):
            this_ent = symtab.get('this')
            rec.merge(this_ent.type)
    return rec


class CheckDataExp(ast.NodeVisitor):
    def __init__(self, s, o):
        self.symtab = s
        self.outtab = o

    def visit_Assign(self, node, _):
        symtab = self.symtab
        dest = node.lhs
        exp = node.rhs
        if isinstance(exp, ast.DataExp):
            dest_ent = symtab.get(dest.value)
            rec = get_dataexp_type(exp, symtab)
            dest_ent.type.update(rec)

    def visit_Send(self, node, _):
        symtab = self.symtab
        outtab = self.outtab
        choice = node.msg.choice
        exp = node.msg.data_exp
        port = node.port

        rec = get_dataexp_type(exp, symtab)
        port_ent = outtab.get(port.value)
        if choice:
            l = choice.value
        else:
            l = 'uniq'
        port_ent.type.merge(types.Choice(variants={l:rec}, tails=[]))

    #--------------------------------------------------
    def generic_visit(self, node, children):
        return None


def build(sync_ast):
    intab = sync_ast.inputs.symtab
    outtab = sync_ast.outputs.symtab

    # Fill types from channel variants to store vars
    var_decls = sync_ast.decls
    symtab = var_decls.symtab
    for decl in [d for d in var_decls.decls if isinstance(d, ast.StoreVar)]:
        choice = decl.type.choice
        port = decl.type.port
        port_ent = intab.get(port.value)
        if choice.value in port_ent.type.variants:
            # Fill store var type from channel variant
            ch_typ = port_ent.type.variants[choice.value]
            decl_ent = symtab.get(decl.name.value)
            decl_ent.type.merge(ch_typ)
        else:
            # Fill variant from store var
            rec = types.Record(labels={}, tails=[types.Variable()])
            port_ent.type.merge(types.Choice(variants={choice.value:rec}, tails=[]))

    ca = CheckAST(intab, outtab)
    ca.traverse(sync_ast)

    #print("---INTAB---")
    #intab.show()
    #print("---OUTTAB---")
    #outtab.show()
