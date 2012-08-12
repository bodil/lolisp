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

def test_conj():
  l = cons(Type("number", 3), nil)
  l = cons(Type("number", 3), l)
  l = cons(Type("number", 1), l)
  l = cons(Type("number", 3), l)
  assert repr(l) == "(3 1 3 3)"
  assert repr(conj(l, Type("number", 7))) == "(3 1 3 3 7)"

class Type(object):
  def __init__(self, type, value, sig = None, token = None):
    self.type = type
    self.value = value
    if sig != None:
      self.sig = sig

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

def test_is_list():
  assert is_list(nil)
  assert is_list(cons(Type("number", 1337), nil))
  assert not is_list(Type("string", "ohai"))

def is_nil(i):
  return is_list(i) and i.is_nil()

def test_is_nil():
  assert is_nil(nil)
  assert not is_nil(Type("string", "ohai"))
  assert not is_nil(cons(Type("number", 1337), nil))

def is_atom(i):
  return is_nil(i) or isinstance(i, Type)

def test_is_atom():
  assert is_atom(nil)
  assert is_atom(Type("string", "ohai"))
  assert not is_atom(cons(Type("number", 1337), nil))
  assert not is_atom("ohai")

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

def test_type_name():
  assert type_name(Type("string", "ohai")) == "string"
  assert type_name(nil) == "nil"
  assert type_name(cons(Type("string", "ohai"), nil)) == "list"

def token_to_type(token):
  if token["type"] == "string":
    return Type("string", token["value"][1:-1], token = token)
  elif token["type"] == "number":
    return Type("number", str2number(token["value"]), token = token)
  else:
    return Type(token["type"], token["value"], token = token)

def mksymbol(name):
  return Type("symbol", name)

def test_mksymbol():
  assert is_symbol(mksymbol("ohai"))
  assert mksymbol("ohai").value == "ohai"

true = mksymbol("true")
false = mksymbol("false")

def mkprimitive(name):
  return Type("primitive", name)

def mkfunc(sig, body):
  return Type("function", body, sig = sig)

def mkmacro(sig, body):
  return Type("macro", body, sig = sig)

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

def test_py_to_type_boolean():
  assert is_symbol(py_to_type(True))
  assert py_to_type(True).value == "true"
  assert is_symbol(py_to_type(False))
  assert py_to_type(False).value == "false"

def test_py_to_type_string():
  assert is_string(py_to_type("ohai"))
  assert py_to_type("ohai").value == "ohai"

def test_py_to_type_number():
  assert is_number(py_to_type(1337))
  assert py_to_type(1337).value == 1337

def test_py_to_type_list():
  assert repr(py_to_type([1,2,3])) == "(1 2 3)"

def test_deep_mklist():
  l = py_to_type([1,[2]])
  assert repr(l) == "(1 (2))"

def test_pprint():
  out = repr(py_to_type([1,2,3,"ohai",True,[1,3,3,7]]))
  assert out == "(1 2 3 \"ohai\" true (1 3 3 7))"
