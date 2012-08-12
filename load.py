from lex import Lexer, ParserError
import lisptypes as types
import pytest

def load(stream):
  stack = []
  top = types.nil
  last = None
  lexer = Lexer(stream)

  for token in lexer:
    if token["type"] == "lparen":
      stack.append(top)
      if last and last["type"] in ["quote", "unquote", "unquote-splice", "deref"]:
        top = types.cons(last["type"], types.nil)
      else:
        top = types.nil
    elif token["type"] == "rparen":
      if len(stack) == 0:
        raise ParserError("rparen without matching lparen", token)
      if not types.is_nil(top) and top.car in ["quote", "unquote", "unquote-splice", "deref"]:
        func = types.mksymbol(top.car)
        sym = top.cdr
        sym = types.cons(sym, types.nil)
        top = types.cons(func, sym)
      top = types.conj(stack.pop(), top)
    elif token["type"] in ["quote", "unquote"]:
      pass
    elif token["type"] == "deref":
      if last["type"] == "unquote":
        token["type"] = "unquote-splice"
    else:
      if last and last["type"] in ["quote", "unquote", "unquote-splice", "deref"]:
        sexp = types.cons(types.token_to_type(token), types.nil)
        sexp = types.cons(types.mksymbol(last["type"]), sexp)
        top = types.conj(top, sexp)
      else:
        top = types.conj(top, types.token_to_type(token))
    last = token

  if len(stack):
    raise ParserError("lparen without matching rparen", last)

  return top

def test_load_empty():
  sexp = load("(())")
  assert repr(sexp) == "((()))"

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
