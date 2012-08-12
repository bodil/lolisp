import lisptypes as types
from load import load
from primitives import Primitives
from errors import LispException
import threading

class Scope(dict):
  def __init__(self, parent = None, extend = {}):
    dict.__init__(self)
    self.parent = parent
    self.lock = threading.Lock()
    self.extend(extend)

  def define(self, symbol, value):
    if types.is_symbol(symbol):
      symbol = symbol.value
    self.lock.acquire()
    self[symbol] = value
    self.lock.release()
    return value

  def extend(self, d):
    for key in d:
      self.define(key, d[key])

  def lookup(self, key):
    rv = None
    self.lock.acquire()
    if self.has_key(key):
      rv = self[key]
    elif self.parent:
      rv = self.parent.lookup(key)
    self.lock.release()
    return rv

class RT(object):
  def __init__(self, ns = None):
    if ns:
      self.ns = ns
    else:
      prims = Primitives(self)

      import primitives.math
      prims.extend(primitives.math)
      import primitives.concurrent
      prims.extend(primitives.concurrent)

      self.ns = Scope(extend = prims)
    self.scope = self.ns

  def clone(self):
    return RT(ns = self.ns)

  def lookup(self, symbol):
    value = self.scope.lookup(symbol.value)
    if value:
      return value
    raise LispException("symbol \"%s\" is undefined" % symbol.value)

  def define(self, symbol, value):
    return self.ns.define(symbol, value)

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
      return func.invoke(args)

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
