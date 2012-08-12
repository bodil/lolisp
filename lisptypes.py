## types.py -- Constructing and checking typed entities

from numbers import Number
from lispmath import str2number

class ConsCell(object):
  def __init__(self, car, cdr):
    self.car = car
    self.cdr = cdr

  def __iter__(self):
    el = self
    while el != nil:
      yield el.car
      el = el.cdr

  def is_nil(self):
    return self.car == None and self.cdr == None

  def is_regular_list(self):
    return self.is_nil() or (isinstance(self.cdr, ConsCell) and self.cdr.is_regular_list(self))

  def __repr__(self):
    if self.is_nil():
      return "nil"
    if isinstance(self.cdr, ConsCell):
      return "(%s)" % " ".join((repr(el) for el in self))
    else:
      return "(%s . %s)" % (repr(self.car), repr(self.cdr))

  def __eq__(self, other):
    if not isinstance(other, ConsCell):
      return False
    return self.car == other.car and self.cdr == other.cdr

cons = ConsCell

nil = cons(None, None)

def conj(l, e):
  if is_nil(l):
    return cons(e, nil)
  def rec(l):
    if l.cdr == nil:
      return cons(l.car, cons(e, nil))
    else:
      return cons(l.car, rec(l.cdr))
  return rec(l)

class Type(object):
  def __init__(self, type, value, sig = None, scope = None, token = None):
    self.type = type
    self.value = value
    if sig != None:
      self.sig = sig
    if scope != None:
      self.scope = scope

  def __repr__(self):
    if self.type == "number":
      return str(self.value)
    elif self.type == "string":
      return '"%s"' % self.value
    elif self.type == "symbol":
      return self.value
    elif self.type == "primitive":
      return "<primitive %s>" % self.value
    elif self.type == "function":
      return "(lambda %s %s)" % (repr(mklist(self.sig)),
                                 " ".join(list(repr(i) for i in self.value)))
    elif self.type == "macro":
      return "(macro %s %s)" % (repr(mklist(self.sig)),
                                 " ".join(list(repr(i) for i in self.value)))
    else:
      return "<UNREPRESENTABLE LISPTYPE \"%s\">" % self.value

  def __eq__(self, other):
    if not isinstance(other, Type):
      return False
    return self.type == other.type and self.value == other.value

def is_list(i):
  return isinstance(i, ConsCell)

def is_nil(i):
  return is_list(i) and i.is_nil()

def is_atomic(i):
  return is_nil(i) or isinstance(i, Type)

def is_symbol(i):
  return isinstance(i, Type) and i.type == "symbol"

def is_number(i):
  return isinstance(i, Type) and i.type == "number"

def is_string(i):
  return isinstance(i, Type) and i.type == "string"

def is_function(i):
  return isinstance(i, Type) and i.type == "function"

def is_primitive(i):
  return isinstance(i, Type) and i.type == "primitive"

def is_macro(i):
  return isinstance(i, Type) and i.type == "macro"

def type_name(i):
  if is_nil(i):
    return "nil"
  elif is_list(i):
    return "list"
  elif isinstance(i, Type):
    return i.type
  else:
    return "unknown"

def token_to_type(token):
  if token["type"] == "string":
    return Type("string", token["value"][1:-1], token = token)
  elif token["type"] == "number":
    return Type("number", str2number(token["value"]), token = token)
  else:
    return Type(token["type"], token["value"], token = token)

def mksymbol(name):
  return Type("symbol", name)

true = mksymbol("true")
false = mksymbol("false")

def mkprimitive(name, func):
  p = Type("primitive", name)
  p.invoke = func
  return p

def mkfunc(sig, body, scope):
  return Type("function", body, sig = sig, scope = scope)

def mkmacro(sig, body, scope):
  return Type("macro", body, sig = sig, scope = scope)

def mklist(a):
  l = nil
  for el in reversed(a):
    if isinstance(el, list):
      el = mklist(el)
    l = cons(el, l)
  return l

def py_to_type(obj):
  if isinstance(obj, bool):
    return true if obj else false
  elif isinstance(obj, str):
    return Type("string", obj)
  elif isinstance(obj, Number):
    return Type("number", obj)
  elif isinstance(obj, list):
    return mklist(map(py_to_type, obj))
  else:
    raise TypeError("object %s cannot be converted to a Lisp type" % repr(obj))
