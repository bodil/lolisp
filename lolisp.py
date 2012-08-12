#!/usr/bin/env pypy

from load import load
from rt import RT, LispException
import lisptypes as types

import sys, os.path
from argparse import ArgumentParser

arg_parser = ArgumentParser(description = "Run you a lisp!")
arg_parser.add_argument("file", nargs = "?", help = "Lolisp source file to run")
args = arg_parser.parse_args()

rt = RT()
rt.load(file(os.path.join(sys.path[0], "rt.loli")))

if args.file:
  rt.load(file(args.file))
else:
  while 1:
    print ">>> ",
    s = sys.stdin.readline()
    if not s:
      break
    sexps = load(s)
    for sexp in sexps:
      try:
        print "=> %s" % repr(rt.execute(sexp))
      except LispException as e:
        print "***", str(e)
