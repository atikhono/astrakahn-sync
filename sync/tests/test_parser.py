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


if __name__ == 'main':
    unittest.main()
