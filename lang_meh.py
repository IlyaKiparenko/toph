import sys
import os
#from collections import namedtuple
from dataclasses import dataclass

class Context:
    def __init__(self, name, parent=None):
        self.name = name
        self.d_dict = {}
        self.parent = parent

    def get(self, name):
        if name in self.d_dict:
            return self.d_dict[name]
        elif self.parent:
            return self.parent.get(name)
        raise KeyError

    def set(self, name, value):
        self.d_dict[name] = value

    def print(self, indent=''):
        print (f"{indent}Context ({self.name}) {{")
        n_indent = indent + '  '
        for key, value in self.d_dict.items():
            print(n_indent, key, ' = ', value, sep='')
        if self.parent:
            self.parent.print(n_indent)
        print(f"{indent}}}")

c1 = Context('first')
c1.set ('a', 1)
c1.set ('b', 2)

c2 = Context('second', c1)
c2.set ('a', 3)
c2.set ('c', 'Hello')

print("hello")
c2.print()
print(c2.get('a'))
