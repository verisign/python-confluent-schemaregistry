import sys
import os
import os.path

'''
Hacky way to ensure that we are loading the code that we
intend to test.
'''

test_dir = os.path.dirname(os.path.realpath(__file__))
parent = os.path.join(test_dir, '..')
sys.path.insert(0, parent)
