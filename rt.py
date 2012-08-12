import lisptypes as types
from load import load
from primitives import Primitives
from errors import LispException

class Scope(dict):
  def __init__(self, parent):
    dict.__init__(self)
    self.parent = parent

  def lookup(self, key):
    if self.has_key(key):
      return self[key]
    if self.parent:
      return self.parent.lookup(key)
    else:
      return None

class RT(object):
  def __init__(self):
    self.ns = Scope(None)
    self.scope = self.ns

    self.define("nil", types.nil)
    self.define("true", types.true)
    self.define("false", types.false)
    self.define("else", types.true)

    self.primitives = Primitives(self)
    import primitives.math
    self.primitives.extend(primitives.math)

  def lookup(self, symbol):
    value = self.scope.lookup(symbol.value)
    if value:
      return value
    if self.primitives.has_key(symbol.value):
      return types.mkprimitive(symbol.value)
    raise LispException("symbol \"%s\" is undefined" % symbol.value)

  def define(self, symbol, value):
    if types.is_symbol(symbol):
      symbol = symbol.value
    self.ns[symbol] = value
    return value

  def eval(self, exp):
    """
    If exp is a list, execute it as a function call.
    If exp is a symbol, resolve it.
    Else, return it as is.
    """
    if types.is_list(exp) and not types.is_nil(exp):
      return self.execute(exp)
    elif types.is_symbol(exp):
      return self.lookup(exp)
    else:
      return exp

  def invoke(self, func, args):
    args = list(args)

    if types.is_primitive(func):
      return self.primitives[func.value](args)

    closure = Scope(self.scope)
    args = list(args)

    try:
      rest = list((i.value for i in func.sig)).index("&")
    except ValueError:
      rest = -1
      if len(args) != len(func.sig):
        raise LispException("%s takes %d arguments, %d given" %
                            (types.type_name(func),
                             len(func.sig), len(args)))
    else:
      if len(args) < rest:
        raise LispException("%s takes at least %d arguments, %d given" %
                            (types.type_name(func), rest, len(args)))

    for i in xrange(len(args)):
      if func.sig[i].value == "&":
        closure[func.sig[rest+1].value] = types.mklist(args[rest:])
        rest = -1
        break
      else:
        closure[func.sig[i].value] = args[i]
    if rest >= 0:
      closure[func.sig[rest+1].value] = types.nil

    self.scope = closure

    rv = types.nil
    for sexp in func.value:
      rv = self.execute(sexp)

    self.scope = self.scope.parent
    del closure

    return rv

  def execute(self, sexp):
    if types.is_atom(sexp):
      return self.eval(sexp)

    if types.is_nil(sexp):
      return sexp

    func = self.eval(sexp.car)
    args = list(sexp.cdr)

    if types.is_primitive(func):
      return self.invoke(func, args)

    if types.is_macro(func):
      return self.eval(self.invoke(func, args))

    if types.is_function(func):
      return self.invoke(func, (self.eval(arg) for arg in args))

    raise LispException("%s is not callable" % repr(func), sexp)

  def load(self, stream):
    for sexp in load(stream):
      self.execute(sexp)
