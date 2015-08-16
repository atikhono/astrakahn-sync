#!/usr/bin/env python3

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(__file__) + '/../../..')

import compiler.sync as sync
import compiler.sync.exception as exn


class TestIntabError(unittest.TestCase):
    def test_check_ast_send(self):
        try:
            ast = sync.process('synch id (a | b) {\
store ?v.a g;\
start {\
    on:\
        a {\
            send this => c;\
        }\
}}')
            assert(1 != 1)
        except exn.NotDeclaredError as err:
            self.assertTrue(err.msg == "output channel 'c' not declared")

    def test_check_ast_store_type(self):
        try:
            ast = sync.process('synch id (a | b) {\
store ?v.c g;\
start {\
    on:\
        a {}\
}}')
            assert(1 != 1)
        except exn.NotDeclaredError as err:
            self.assertTrue(err.msg == "input channel 'c' not declared")

    def test_check_ast_trans_01(self):
        try:
            ast = sync.process('synch id (a | b) {\
start {\
    on:\
        z {}\
}}')
            assert(1 != 1)
        except exn.NotDeclaredError as err:
            self.assertTrue(err.msg == "input channel 'z' not declared")

    def test_check_exp_assign_01(self):
        try:
            ast = sync.process('synch id (a | b) {\
store ?v.a j;\
start {\
    on:\
        a {\
            set n = [1], m = j;\
        }\
}}')
            assert(1 != 1)
        except exn.NotDeclaredError as err:
            self.assertTrue(err.msg == "variable 'm' not declared")

    def test_check_exp_assign_02(self):
        try:
            ast = sync.process('synch id (a | b) {\
start {\
    on:\
        a.(x) {\
            set x = [1];\
        }\
}}')
            assert(1 != 1)
        except exn.NotAssignableError as err:
            self.assertTrue(err.msg == "cannot assign to variable 'x' declared")

    def test_check_exp_assign_03(self):
        try:
            ast = sync.process('synch id (a | b) {\
state int(10) x;\
store a j;\
start {\
    on:\
        a {\
            set x = j;\
        }\
}}')
            assert(1 != 1)
        except exn.TypeError as err:
            self.assertTrue(err.msg == "Type mismatch as data expression"
                " assigned to variable 'x' declared integer")

    def test_check_exp_assign_04(self):
        try:
            ast = sync.process('synch id (a | b) {\
store a j;\
start {\
    on:\
        a {\
            set j = [1];\
        }\
}}')
            assert(1 != 1)
        except exn.TypeError as err:
            self.assertTrue(err.msg == "Type mismatch as integer expression"
                " assigned to variable 'j' declared data")

    def test_check_exp_dataexp_01(self):
        try:
            ast = sync.process('synch id (a | b) {\
store a j;\
start {\
    on:\
        a {\
            set j = x;\
        }\
}}')
            assert(1 != 1)
        except exn.NotDeclaredError as err:
            self.assertTrue(err.msg == "variable 'x' not declared")

    def test_check_exp_dataexp_02(self):
        try:
            ast = sync.process('synch id (a | b) {\
state int(10) y;\
store a j;\
start {\
    on:\
        a.(x) {\
            set y = [x], j = \'x || x;\
        }\
}}')
            assert(1 != 1)
        except exn.TypeError as err:
            self.assertTrue(err.msg == "Type mismatch as variable 'x' found in"
                " data expression declared integer")

    def test_check_exp_dataexp_03(self):
        try:
            ast = sync.process('synch id (a | b) {\
store a j;\
start {\
    on:\
        a {\
            set j = \'x;\
        }\
}}')
            assert(1 != 1)
        except exn.NotDeclaredError as err:
            self.assertTrue(err.msg == "variable 'x' not declared")

    def test_check_exp_intexp_01(self):
        try:
            ast = sync.process('synch id (a | b) {\
state int(1) a;\
start {\
    on:\
        a {\
            set n = [1+a+x];\
        }\
}}')
            assert(1 != 1)
        except exn.NotDeclaredError as err:
            self.assertTrue(err.msg == "variable 'x' not declared")

    def test_check_exp_intexp_02(self):
        try:
            ast = sync.process('synch id (a | b) {\
store a j;\
start {\
    on:\
        a & [j] {\
        }\
}}')
            assert(1 != 1)
        except exn.TypeError as err:
            self.assertTrue(err.msg == "Type mismatch as variable 'j' found in"
                " integer expression declared data")

    def test_check_exp_intexp_03(self):
        try:
            ast = sync.process('synch id (a | b) {\
store a j;\
start {\
    on:\
        a.(y) {\
            set j = y, n = [y];\
        }\
}}')
            assert(1 != 1)
        except exn.TypeError as err:
            self.assertTrue(err.msg == "Type mismatch as variable 'y' found in"
                " integer expression declared data")


if __name__ == 'main':
    unittest.main()
