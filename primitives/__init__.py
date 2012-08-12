import lisptypes as types
from load import load
from errors import LispException

def is_splice(sexp):
  return (not types.is_nil(sexp)) and types.is_list(sexp) and types.is_symbol(sexp.car) and sexp.car.value == "unquote-splice"

def signature(*params):
  def decorate(func):
    if len(params) == 2:
      (name, sig) = params
    else:
      name = func.__name__.replace("_", "-")
      sig = params[0]
    def wrap(self, scope, args):
      args = self.parse_sig(scope, name, args, sig)
      return func(self, scope, args)
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
    def wrap(primitives, scope, args):
      args = primitives.parse_sig(scope, name, args, sig)
      return func(primitives, scope, args)
    wrap.primitive_name = name
    wrap.external = True
    wrap.__name__ = func.__name__
    return wrap
  return decorate

def wrap_external(primitives, fn):
  return lambda scope, args: fn(primitives, scope, args)

def match_class(classes, name):
  for c in classes:
    if name == c.__name__ or match_class(c.__bases__, name):
      return True
  return False

class Primitives(dict):
  def __init__(self, rt):
    self.rt = rt
    self["nil"] = types.nil
    self["true"] = types.true
    self["false"] = types.false
    self["else"] = types.true
    self.extend(self)

  def extend(self, package):
    for key in dir(package):
      fn = getattr(package, key)
      if hasattr(fn, "primitive_name"):
        name = fn.primitive_name
        if hasattr(fn, "external"):
          fn = wrap_external(self, fn)
        self[name] = types.mkprimitive(name, fn)

  def parse_sig(self, scope, fn, args, signature):
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
        arg = self.rt.eval(scope, arg)

      if sig != "any":
        matched = False
        for t in sig.split("|"):
          if t.islower():
            test = getattr(types, "is_%s" % t)
            if test(arg):
              matched = True
          else:
            if match_class([arg.__class__], t):
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
      out.append(map(lambda x: self.rt.eval(scope, x), args))
    elif rest == "&":
      out.append(args)

    return out

  def _unquote(self, scope, sexp):
    if types.is_list(sexp) and not types.is_nil(sexp):
      if types.is_symbol(sexp.car) and sexp.car.value == "unquote":
        return self.rt.eval(scope, sexp.cdr.car)

      out = types.nil
      for el in sexp:
        if is_splice(el):
          for splice in self.rt.eval(scope, el.cdr.car):
            out = types.conj(out, splice)
        else:
          out = types.conj(out, self._unquote(scope, el))
      return out
    else:
      return sexp

  @signature("any")
  def quote(self, scope, args):
    return self._unquote(scope, args[0])

  @signature("@any")
  def unquote(self, scope, args):
    return args[0]

  @signature("any")
  def unquote_splice(self, scope, args):
    raise LispException("you can't use unquote-splice outside of quote")

  @signature("atomic?", "@any")
  def atomic(self, scope, args):
    return types.py_to_type(types.is_atomic(args[0]))

  @signature("@any @any")
  def cons(self, scope, args):
    (car, cdr) = args
    return types.cons(car, cdr)

  @signature("@list")
  def car(self, scope, args):
    if types.is_nil(args[0]):
      return types.nil
    return args[0].car

  @signature("@list")
  def cdr(self, scope, args):
    if types.is_nil(args[0]):
      return types.nil
    return args[0].cdr

  @signature("symbol @any")
  def define(self, scope, args):
    return self.rt.define(args[0], args[1])

  @signature("=", "@any @any")
  def equals(self, scope, args):
    return types.py_to_type(args[0] == args[1])

  @signature("*")
  def cond(self, scope, args):
    for i in xrange(len(args)):
      sexp = args[i]
      if not types.is_list(sexp):
        raise LispException("argument %d of cond must be list, is %s" %
                            (i + 1, types.type_name(sexp)))
      if types.is_nil(sexp) or types.is_nil(sexp.cdr):
        raise LispException("argument %d of cond must have a length of >= 2" % (i + 1))
    for rule in args:
      test = self.rt.eval(scope, rule.car)
      if test != types.true and test != types.false:
        raise LispException("expr %s does not evaluate to a boolean" % repr(rule.car))
      if test == types.true:
        for sexp in rule.cdr:
          rv = self.rt.eval(scope, sexp)
        return rv

    return types.nil

  @signature("print", "*")
  def print_args(self, scope, args):
    args = map(lambda x: self.rt.eval(scope, x), args)
    args = (i.value if types.is_string(i) else repr(i) for i in args)
    print " ".join(args)
    return types.nil

  @signature("load", "@string")
  def load_string(self, scope, args):
    return load(args[0].value).car

  @signature("@any")
  def eval(self, scope, args):
    return self.rt.eval(scope, args[0])

  @signature("@function|primitive @list")
  def apply(self, scope, args):
    quoted = (types.cons(types.mksymbol("quote"), types.cons(i, types.nil)) for i in args[1])
    return self.rt.invoke(scope, args[0], list(quoted))

  @signature("lambda", "list &")
  def lambda_func(self, scope, args):
    sig = list(args[0])
    body = types.mklist(args[1])

    for arg in sig:
      if not types.is_symbol(arg):
        raise LispException("argument 1 of lambda must be a list of symbols, found %s" % types.type_name(arg))

    return types.mkfunc(sig, body, scope)

  @signature("list &")
  def macro(self, scope, args):
    sig = list(args[0])
    body = types.mklist(args[1])

    for arg in sig:
      if not types.is_symbol(arg):
        raise LispException("argument 1 of lambda must be a list of symbols, found %s" % types.type_name(arg))

    return types.mkmacro(sig, body, scope)

  @signature("@callable @any @list")
  def foldr(self, scope, args):
    (func, acc, l) = args
    for el in l:
      acc = self.rt.invoke(scope, func, [acc, el])
    return acc

  @signature("@callable @any @list")
  def foldl(self, scope, args):
    (func, acc, l) = args
    for el in reversed(list(l)):
      acc = self.rt.invoke(scope, func, [acc, el])
    return acc
