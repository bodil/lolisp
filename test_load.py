import pytest
from load import *

def test_load_empty():
  sexp = load("(())")
  assert repr(sexp) == "((nil))"

def test_load_mixed():
  sexp = load("(a b c (1 2 3) \"foo\")")
  assert repr(sexp) == "((a b c (1 2 3) \"foo\"))"

def test_unbalanced_rparen():
  with pytest.raises(ParserError):
    sexp = load("(a b c))")

def test_unbalanced_lparen():
  with pytest.raises(ParserError):
    sexp = load("(a b c")

def test_quote():
  sexp = load("(a b c '(1 2 3))")
  assert repr(sexp) == "((a b c (quote (1 2 3))))"

def test_unquote():
  sexp = load("(a b c ~d)")
  assert repr(sexp) == "((a b c (unquote d)))"

def test_unquote_list():
  sexp = load("(a b c ~(1 2 3))")
  assert repr(sexp) == "((a b c (unquote (1 2 3))))"

def test_unquote_splice():
  sexp = load("(a b c ~@d)")
  assert repr(sexp) == "((a b c (unquote-splice d)))"

def test_unquote_splice_list():
  sexp = load("(a b c ~@(1 2 3))")
  assert repr(sexp) == "((a b c (unquote-splice (1 2 3))))"

def test_deref():
  sexp = load("(a b c @d)")
  assert repr(sexp) == "((a b c (deref d)))"

def test_deref_list():
  sexp = load("(a b c @(1 2 3))")
  assert repr(sexp) == "((a b c (deref (1 2 3))))"
