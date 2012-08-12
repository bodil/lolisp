from decimal import Decimal
from fractions import Fraction

def str2number(s):
  if "/" in s:
    return Fraction(s)
  if "." in s:
    return Decimal(s)
  else:
    return long(s)

def promote_array(ns):
  if filter(lambda n: isinstance(n, Fraction), ns):
    return map(Fraction, ns)
  else:
    return ns

def promote_numbers(func):
  def wrap(*args, **kwargs):
    return func(*promote_array(args), **kwargs)
  return wrap

def reduce_num(func, *nums):
  return reduce(func, promote_array(nums))
