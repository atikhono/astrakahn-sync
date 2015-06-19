#!/usr/bin/env python3

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(__file__) + '/../../..')

import compiler.sync as sync
import compiler.sync.exception as exn


class TestParseError(unittest.TestCase):
    def test_eof(self):
        try:
            ast = sync.parse('synch id (a | b) {')
            assert(1 != 1)
        except exn.ParseError as err:
            self.assertFalse(err.coord)
            self.assertTrue(err.msg == "Syntax error")


class TestDuplicatesError(unittest.TestCase):
    def test_input(self):
        try:
            ast = sync.parse('synch id (a, b, a | c) {start {on: a{}}}')
            assert(1 != 1)
        except exn.DuplicatesError as err:
            self.assertTrue(err.msg == "Channel 'a' was previously declared")

    def test_output(self):
        try:
            ast = sync.parse('synch id (a | b, b) {start {on: a{}}}')
            assert(1 != 1)
        except exn.DuplicatesError as err:
            self.assertTrue(err.msg == "Channel 'b' was previously declared")

    def test_decl_store_1(self):
        try:
            ast = sync.parse('synch id (a | b) {store ?v.a ma,ma; start {on: a{}}}')
            assert(1 != 1)
        except exn.DuplicatesError as err:
            self.assertTrue(err.msg == "Store variable 'ma' was previously declared")

    def test_decl_store_2(self):
        try:
            ast = sync.parse('synch id (a, b | c) {store ?v.a ma; store ?v.b ma; start {on: a{}}}')
            assert(1 != 1)
        except exn.DuplicatesError as err:
            self.assertTrue(err.msg == "Store variable 'ma' was previously declared")

    def test_state_type_1(self):
        try:
            ast = sync.parse('synch id (a | b) {state enum(v,b,v) foo; start {on: a{}}}')
            assert(1 != 1)
        except exn.DuplicatesError as err:
            self.assertTrue(err.msg == "'v' was previously declared")

    def test_state_type_2(self):
        try:
            ast = sync.parse('synch id (a | b) {state int(1) x; state enum(x,b) foo; start {on: a{}}}')
            assert(1 != 1)
        except exn.DuplicatesError as err:
            self.assertTrue(err.msg == "'x' was previously declared")

    def test_state_type_3(self):
        try:
            ast = sync.parse('synch id (a | b) {store ?v.a x; state enum(x,b) foo; start {on: a{}}}')
            assert(1 != 1)
        except exn.DuplicatesError as err:
            self.assertTrue(err.msg == "'x' was previously declared")

    def test_state_type_4(self):
        try:
            ast = sync.parse('synch id (a | b) {store ?v.a x; state int(1) x; start {on: a{}}}')
            assert(1 != 1)
        except exn.DuplicatesError as err:
            self.assertTrue(err.msg == "'x' was previously declared")

    def test_cond_datamsg_1(self):
        try:
            ast = sync.parse('synch id (a | b) {start {on: a.(x, y, x || t){}}}')
            assert(1 != 1)
        except exn.DuplicatesError as err:
            self.assertTrue(err.msg == "'x' was previously declared")

    def test_cond_datamsg_2(self):
        try:
            ast = sync.parse('synch id (a | b) {start {on: a.(x, y || x){}}}')
            assert(1 != 1)
        except exn.DuplicatesError as err:
            self.assertTrue(err.msg == "'x' was previously declared")

    def test_cond_datamsg_3(self):
        try:
            ast = sync.parse('synch id (a | b) {state int(1) x; start {on: a.(x, y || t){}}}')
            assert(1 != 1)
        except exn.DuplicatesError as err:
            self.assertTrue(err.msg == "'x' was previously declared")

    def test_cond_datamsg_4(self):
        try:
            ast = sync.parse('synch id (a | b) {store ?v.a x; start {on: a.(x, y || t){}}}')
            assert(1 != 1)
        except exn.DuplicatesError as err:
            self.assertTrue(err.msg == "'x' was previously declared")

    def test_cond_datamsg_5(self):
        try:
            ast = sync.parse('synch id (a | b) {start {on: a.?v(x, y, x || t){}}}')
            assert(1 != 1)
        except exn.DuplicatesError as err:
            self.assertTrue(err.msg == "'x' was previously declared")

    def test_cond_datamsg_6(self):
        try:
            ast = sync.parse('synch id (a | b) {start {on: a.?v(x, y || x){}}}')
            assert(1 != 1)
        except exn.DuplicatesError as err:
            self.assertTrue(err.msg == "'x' was previously declared")

    def test_cond_datamsg_7(self):
        try:
            ast = sync.parse('synch id (a | b) {state int(1) x; start {on: a.?v(x, y || t){}}}')
            assert(1 != 1)
        except exn.DuplicatesError as err:
            self.assertTrue(err.msg == "'x' was previously declared")

    def test_cond_datamsg_8(self):
        try:
            ast = sync.parse('synch id (a | b) {store ?v.a x; start {on: a.?v(x, y || t){}}}')
            assert(1 != 1)
        except exn.DuplicatesError as err:
            self.assertTrue(err.msg == "'x' was previously declared")


if __name__ == 'main':
    unittest.main()
