#!/usr/bin/env python3

import sys
#sys.path.insert(0, '.')

import unittest


suite = unittest.TestLoader().loadTestsFromNames(
        [
            'test_parser',
        ]
    )

testresult = unittest.TextTestRunner(verbosity=1).run(suite)
sys.exit(0 if testresult.wasSuccessful() else 1)
