import string
import sys

a = sys.stdin.read()
print string.split(a, '_________________________________________________________________')[1]
