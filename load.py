from lex import Lexer, ParserError
import lisptypes as types

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
      if last and last["type"] == "unquote":
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
