import lisptypes as types
from errors import LispException
from primitives import extend
import lispmath as m
from fractions import Fraction
from decimal import Decimal

def reduce_func(name, reducer):
  @extend(name, "@&")
  def func(self, scope, args):
    args = args[0]
    for i in xrange(len(args)):
      n = args[i]
      if not types.is_number(n):
        raise LispException("argument %d of %s must be number, was %s" %
                            (i + 1, func.__name__,
                             types.type_name(n)))
    return types.py_to_type(m.reduce_num(reducer,
                                         *(n.value for n in args)))
  return func

plus = reduce_func("+", lambda a, b: a + b)
minus = reduce_func("-", lambda a, b: a - b)
mul = reduce_func("*", lambda a, b: a * b)
div = reduce_func("/", lambda a, b: a / b)
rem = reduce_func("rem", lambda a, b: a % b)

@extend("number?", "@any")
def is_number(self, scope, args):
  return types.py_to_type(types.is_number(args[0]))

@extend("int?", "@any")
def is_int(self, scope, args):
  return types.py_to_type(types.is_number(args[0]) and isinstance(args[0].value, long))

@extend("decimal?", "@any")
def is_decimal(self, scope, args):
  return types.py_to_type(types.is_number(args[0]) and isinstance(args[0].value, Decimal))

@extend("fraction?", "@any")
def is_fraction(self, scope, args):
  return types.py_to_type(types.is_number(args[0]) and isinstance(args[0].value, Fraction))

@extend("<", "@number @number")
def less_than(self, scope, args):
  return types.py_to_type(args[0].value < args[1].value)

@extend("<=", "@number @number")
def less_than_or_equal(self, scope, args):
  return types.py_to_type(args[0].value <= args[1].value)

@extend(">", "@number @number")
def greater_than(self, scope, args):
  return types.py_to_type(args[0].value > args[1].value)

@extend(">=", "@number @number")
def greater_than_or_equal(self, scope, args):
  return types.py_to_type(args[0].value >= args[1].value)
