#!/usr/bin/env python3

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(__file__) + '/../../..')

import compiler.sync as sync
import compiler.sync.exception as exn
import compiler.sync.symtab as symtab
import compiler.sync.types as types


# Extract a symtab list from ast.
class AstSymtab(sync.ast.NodeVisitor):
    def __init__(self):
        self.l = []

    def visit_Trans(self, node, _):
        self.l.append(node.symtab)

    def generic_visit(self, node, _):
        return None

class TestOuttabError(unittest.TestCase):
    def test_check_ast_send(self):
        ast = sync.process('synch id (a | b) {\
store ?v.a j;\
start {\
    on:\
        a.?w(x,y) {\
            goto s1;\
        }\
        a.?q {\
        }}\
s1 {\
    on:\
        a.?r(x || t) {\
        }\
}}')
        intab = ast.inputs.symtab
        a_ent = intab.get('a')
        self.assertFalse(a_ent is None)
        self.assertTrue(isinstance(a_ent.type, types.Choice))
        
        a_variants = a_ent.type.variants
        self.assertTrue('w' in a_variants)
        w_rec = a_variants['w']
        self.assertTrue('x' in w_rec.labels)
        self.assertTrue('y' in w_rec.labels)
        self.assertTrue(len(w_rec.labels) == 2)

        self.assertTrue('q' in a_variants)
        q_rec = a_variants['q']
        self.assertTrue(len(q_rec.labels) == 0)
        self.assertTrue(len(q_rec.tails) == 1)
        
        self.assertTrue('r' in a_variants)
        r_rec = a_variants['r']
        self.assertTrue(len(r_rec.labels) == 1)
        self.assertTrue('x' in r_rec.labels)
        self.assertTrue(len(r_rec.tails) == 1)

    def test_check_data_exp_assign(self):
        ast = sync.process('synch id (a | b) {\
store a j;\
start {\
    on:\
        a {\
            set j = this || x:[1];\
        }\
}}')
        symtab = ast.decls.symtab
        j_ent = symtab.get('j')
        self.assertFalse(j_ent is None)
        j_rec = j_ent.type
        self.assertTrue(len(j_rec.labels) == 1)
        self.assertTrue('x' in j_rec.labels)

    def test_visit_trans(self):
        ast = sync.process('synch id (a | b) {\
store ?v.a m, j;\
start {\
    on:\
        a.?v(x, y || t) {\
            set m = this;\
        }\
        a.?v(z || h) {\
            set j = this;\
        }\
}}')
        st = AstSymtab()
        st.traverse(ast)
        symtabs = st.l
        
        m_ent = symtabs[0].get('m')
        j_ent = symtabs[1].get('j')
        self.assertTrue(m_ent.type.show() == j_ent.type.show())
        
        this_0 = symtabs[0].get('this')
        this_1 = symtabs[1].get('this')
        self.assertTrue(this_0.type.show() == this_1.type.show())
        
        t_ent = symtabs[0].get('t')
        self.assertTrue(len(t_ent.type.labels) == 1)
        self.assertTrue('z' in t_ent.type.labels)
        self.assertTrue(t_ent.type.labels['z'].show() == this_0.type.labels['z'].show())
        self.assertTrue(len(t_ent.type.tails) == 1)
        self.assertTrue(t_ent.type.tails[0].show() == this_0.type.tails[0].show())

        h_ent = symtabs[1].get('h')
        self.assertTrue(len(h_ent.type.labels) == 2)
        self.assertTrue('x' in h_ent.type.labels)
        self.assertTrue(h_ent.type.labels['x'].show() == this_0.type.labels['x'].show())
        self.assertTrue('y' in h_ent.type.labels)
        self.assertTrue(h_ent.type.labels['y'].show() == this_0.type.labels['y'].show())
        self.assertTrue(len(h_ent.type.tails) == 1)
        self.assertTrue(h_ent.type.tails[0].show() == this_0.type.tails[0].show())

    # Is this test valid at all?
    # Should 'a'['uniq'] be { x:Int, y:Int || t }
    def test_get_dataexp_type(self):
        ast = sync.process('synch id (a | b) {\
start {\
    on:\
        a {\
            send (x:[1] || y:[1]) => b;\
        }\
        a.(x, y || t) {\
            send (this) => b;\
        }\
}}')
        outtab = ast.outputs.symtab
        b_ent = outtab.get('b')
        self.assertFalse(b_ent is None)
        self.assertTrue('uniq' in b_ent.type.variants)

        u_rec = b_ent.type.variants['uniq']
        self.assertTrue(len(u_rec.labels) == 2)
        self.assertTrue('x' in u_rec.labels)
        self.assertTrue(u_rec.labels['x'].show() == "Int(0)")
        self.assertTrue('y' in u_rec.labels)
        self.assertTrue(u_rec.labels['y'].show() == "Int(0)")
        self.assertTrue(len(u_rec.tails) == 1)
        
    def test_get_dataexp_type(self):
        ast = sync.process('synch a (a | b){\
store ?v.a j;\
start {\
    on:\
        a.?v(y, w || t) & [t+w]{\
            set j = \'w || z:[0];\
        }\
}}')
        symtab = ast.decls.symtab
        j_ent = symtab.get('j')
        self.assertFalse(j_ent is None)
        # { 'y':$__var_5dvq8z, 'z':Int(0), 't':Int(0), 'w':Int(0) }
        self.assertTrue(len(j_ent.type.labels) == 4)
        self.assertTrue('y' in j_ent.type.labels)
        self.assertTrue('z' in j_ent.type.labels)
        self.assertTrue(j_ent.type.labels['z'].show() == "Int(0)")
        self.assertTrue('t' in j_ent.type.labels)
        self.assertTrue(j_ent.type.labels['t'].show() == "Int(0)")
        self.assertTrue('w' in j_ent.type.labels)
        self.assertTrue(j_ent.type.labels['w'].show() == "Int(0)")
        self.assertTrue(len(j_ent.type.tails) == 0)

        st = AstSymtab()
        st.traverse(ast)
        symtabs = st.l
        this_ent = symtabs[0].get('this')
        self.assertFalse(this_ent is None)
        self.assertTrue(len(this_ent.type.labels) == 3)
        self.assertTrue('y' in this_ent.type.labels)
        self.assertTrue('t' in this_ent.type.labels)
        self.assertTrue(this_ent.type.labels['t'].show() == "Int(0)")
        self.assertTrue('w' in this_ent.type.labels)
        self.assertTrue(this_ent.type.labels['w'].show() == "Int(0)")
        self.assertTrue(len(this_ent.type.tails) == 0)




if __name__ == 'main':
    unittest.main()
