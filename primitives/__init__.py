import lisptypes as types
from load import load
from errors import LispException

import pytest

def is_splice(sexp):
  return (not types.is_nil(sexp)) and types.is_list(sexp) and types.is_symbol(sexp.car) and sexp.car.value == "unquote-splice"

def signature(*params):
  def decorate(func):
    if len(params) == 2:
      (name, sig) = params
    else:
      name = func.__name__.replace("_", "-")
      sig = params[0]
    def wrap(self, args):
      args = self.parse_sig(name, args, sig)
      return func(self, args)
    wrap.primitive_name = name
    wrap.__name__ = func.__name__
    return wrap
  return decorate

def extend(*params):
  def decorate(func):
    if len(params) == 2:
      (name, sig) = params
    else:
      name = func.__name__.replace("_", "-")
      sig = params[0]
    def wrap(primitives, args):
      args = primitives.parse_sig(name, args, sig)
      return func(primitives, args)
    wrap.primitive_name = name
    wrap.external = True
    wrap.__name__ = func.__name__
    return wrap
  return decorate

def wrap_external(primitives, fn):
  return lambda args: fn(primitives, args)

class Primitives(dict):
  def __init__(self, rt):
    self.rt = rt
    self.extend(self)

  def extend(self, package):
    for key in dir(package):
      fn = getattr(package, key)
      if hasattr(fn, "primitive_name"):
        if hasattr(fn, "external"):
          self[fn.primitive_name] = wrap_external(self, fn)
        else:
          self[fn.primitive_name] = fn

  def parse_sig(self, fn, args, signature):
    if signature == "*":
      return args

    out = []
    rest = False
    sigs = signature.split(" ")
    if sigs[-1] in ["&", "@&"]:
      rest = sigs[-1]
      sigs = sigs[:-1]
    else:
      if len(sigs) != len(args):
        raise LispException("%s takes %d arguments, %d given" %
                            (fn, len(sigs), len(args)))
    for sig in sigs:
      if not len(args):
        raise LispException("%s takes %s%d arguments, %d given" %
                            (fn, "at least " if rest else "",
                             len(sigs) + 1, len(out)))
      if "callable" in sig:
        sig = sig.replace("callable", "function|macro|primitive")
      arg = args[0]
      args = args[1:]
      if sig[0] == "@":
        sig = sig[1:]
        arg = self.rt.eval(arg)

      if sig != "any":
        matched = False
        for t in sig.split("|"):
          test = getattr(types, "is_%s" % t)
          if test(arg):
            matched = True
        if not matched:
          raise LispException("argument %d of %s must be %s, was %s" %
                              (len(out) + 1, fn, sig,
                               types.type_name(arg)))

      out.append(arg)

    if rest and not len(args):
      raise LispException("%s takes %s%d arguments, %d given" %
                          (fn, "at least " if rest else "",
                           len(sigs) + 1, len(out)))
    if rest == "@&":
      out.append(map(self.rt.eval, args))
    elif rest == "&":
      out.append(args)

    return out

  def _unquote(self, sexp):
    if types.is_list(sexp) and not types.is_nil(sexp):
      if types.is_symbol(sexp.car) and sexp.car.value == "unquote":
        return self.rt.eval(sexp.cdr.car)

      out = types.nil
      for el in sexp:
        if is_splice(el):
          for splice in self.rt.eval(el.cdr.car):
            out = types.conj(out, splice)
        else:
          out = types.conj(out, self._unquote(el))
      return out
    else:
      return sexp

  @signature("any")
  def quote(self, args):
    return self._unquote(args[0])

  @signature("@any")
  def unquote(self, args):
    return args[0]

  @signature("any")
  def unquote_splice(self, args):
    raise LispException("you can't use unquote-splice outside of quote")

  @signature("@any")
  def atom(self, args):
    return types.py_to_type(types.is_atom(args[0]))

  @signature("@any @any")
  def cons(self, args):
    (car, cdr) = args
    return types.cons(car, cdr)

  @signature("@list")
  def car(self, args):
    if types.is_nil(args[0]):
      return types.nil
    return args[0].car

  @signature("@list")
  def cdr(self, args):
    if types.is_nil(args[0]):
      return types.nil
    return args[0].cdr

  @signature("symbol @any")
  def define(self, args):
    return self.rt.define(args[0], args[1])

  @signature("=", "@any @any")
  def equals(self, args):
    return types.py_to_type(args[0] == args[1])

  @signature("*")
  def cond(self, args):
    for i in xrange(len(args)):
      sexp = args[i]
      if not types.is_list(sexp):
        raise LispException("argument %d of cond must be list, is %s" %
                            (i + 1, types.type_name(sexp)))
      if types.is_nil(sexp) or types.is_nil(sexp.cdr):
        raise LispException("argument %d of cond must have a length of >= 2" % (i + 1))
    for rule in args:
      test = self.rt.eval(rule.car)
      if test != types.true and test != types.false:
        raise LispException("expr %s does not evaluate to a boolean" % repr(rule.car))
      if test == types.true:
        for sexp in rule.cdr:
          rv = self.rt.eval(sexp)
        return rv

    return types.nil

  @signature("print", "*")
  def print_args(self, args):
    args = map(self.rt.eval, args)
    args = (i.value if types.is_string(i) else repr(i) for i in args)
    print " ".join(args)
    return types.nil

  @signature("load", "@string")
  def load_string(self, args):
    return load(args[0].value).car

  @signature("@any")
  def eval(self, args):
    return self.rt.eval(args[0])

  @signature("@function|primitive @list")
  def apply(self, args):
    quoted = (types.cons(types.mksymbol("quote"), types.cons(i, types.nil)) for i in args[1])
    return self.rt.invoke(args[0], list(quoted))

  @signature("lambda", "list &")
  def lambda_func(self, args):
    sig = list(args[0])
    body = types.mklist(args[1])

    for arg in sig:
      if not types.is_symbol(arg):
        raise LispException("argument 1 of lambda must be a list of symbols, found %s" % types.type_name(arg))

    return types.mkfunc(sig, body)

  @signature("list &")
  def macro(self, args):
    sig = list(args[0])
    body = types.mklist(args[1])

    for arg in sig:
      if not types.is_symbol(arg):
        raise LispException("argument 1 of lambda must be a list of symbols, found %s" % types.type_name(arg))

    return types.mkmacro(sig, body)

  @signature("@callable @any @list")
  def foldr(self, args):
    (func, acc, l) = args
    for el in l:
      acc = self.rt.invoke(func, [acc, el])
    return acc

  @signature("@callable @any @list")
  def foldl(self, args):
    (func, acc, l) = args
    for el in reversed(list(l)):
      acc = self.rt.invoke(func, [acc, el])
    return acc



def signature_fixture():
  from rt import RT
  rt = RT()
  invoke = lambda func, args: func(rt.primitives, args)
  invoke.rt = rt
  return invoke

def test_signature_passthrough():
  invoke = signature_fixture()
  @signature("*")
  def passthrough(self, args):
    assert args == ["foo", "bar"]
  invoke(passthrough, ["foo", "bar"])

def test_signature_type_checking():
  invoke = signature_fixture()
  @signature("string number")
  def type_check(self, args):
    assert types.is_string(args[0])
    assert types.is_number(args[1])
  invoke(type_check, [types.py_to_type("ohai"),
                      types.py_to_type(1337)])
  with pytest.raises(LispException):
    invoke(type_check, [types.py_to_type("ohai")])
  with pytest.raises(LispException):
    invoke(type_check, [types.py_to_type("ohai"),
                        types.py_to_type("x")])
  with pytest.raises(LispException):
    invoke(type_check, [types.py_to_type("ohai"),
                        types.py_to_type(1337),
                        types.py_to_type("noobs")])

def test_signature_argument_resolution():
  invoke = signature_fixture()
  @signature("@any")
  def resolve_arg(self, args):
    assert types.is_nil(args[0])
  invoke(resolve_arg, [types.mksymbol("nil")])
  with pytest.raises(LispException):
    invoke(resolve_arg, [types.mksymbol("not-defined")])

def test_signature_rest_argument():
  invoke = signature_fixture()
  @signature("any &")
  def rest(self, args):
    assert len(args) == 2
    assert types.is_nil(args[0])
    assert isinstance(args[1], list)
    assert args[1] == [types.mksymbol("ohai"),
                       types.mksymbol("noobs")]
  invoke(rest, [types.nil, types.mksymbol("ohai"),
                types.mksymbol("noobs")])

def test_signature_rest_argument_with_resolution():
  invoke = signature_fixture()
  invoke.rt.define("ohai", types.py_to_type(13))
  invoke.rt.define("noobs", types.py_to_type(37))
  @signature("any @&")
  def rest(self, args):
    assert len(args) == 2
    assert types.is_nil(args[0])
    assert isinstance(args[1], list)
    assert args[1] == list(types.py_to_type([13, 37]))
  invoke(rest, [types.nil, types.mksymbol("ohai"),
                types.mksymbol("noobs")])
  with pytest.raises(LispException):
    invoke(rest, [types.nil, types.mksymbol("not-defined")])
