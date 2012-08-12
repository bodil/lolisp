import lisptypes as types
from errors import LispException
from primitives import extend
import lispmath as m
from fractions import Fraction
from decimal import Decimal

def num_args(func):
  def wrap(p, args):
    args = args[0]
    for i in xrange(len(args)):
      n = args[i]
      if not types.is_number(n):
        raise LispException("argument %d of %s must be number, was %s" %
                            (i + 1, func.__name__,
                             types.type_name(n)))
    return func(p, args)
  return wrap

def reduce_func(name, reducer):
  @extend(name, "@&")
  @num_args
  def func(self, args):
    return types.py_to_type(m.reduce_num(reducer,
                                         *(n.value for n in args)))
  return func

plus = reduce_func("+", lambda a, b: a + b)
minus = reduce_func("-", lambda a, b: a - b)
mul = reduce_func("*", lambda a, b: a * b)
div = reduce_func("/", lambda a, b: a / b)
rem = reduce_func("rem", lambda a, b: a % b)

@extend("number?", "@any")
def is_number(self, args):
  return types.py_to_type(types.is_number(args[0]))

@extend("int?", "@any")
def is_int(self, args):
  return types.py_to_type(types.is_number(args[0]) and isinstance(args[0].value, long))

@extend("decimal?", "@any")
def is_decimal(self, args):
  return types.py_to_type(types.is_number(args[0]) and isinstance(args[0].value, Decimal))

@extend("fraction?", "@any")
def is_fraction(self, args):
  return types.py_to_type(types.is_number(args[0]) and isinstance(args[0].value, Fraction))
