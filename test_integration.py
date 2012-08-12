import pytest, sys, os.path
import lisptypes as types
from errors import LispException
from load import load
from rt import RT

rt = RT()
rt.load(rt.ns, file(os.path.join(sys.path[0], "rt.loli")))
rt.ns.define("is", types.mkprimitive("is", lambda s, a: rt.eval(s, a[0])))
forms = load(file(os.path.join(sys.path[0], "tests.loli")))

def pprint_assert(form):
  form = form.cdr.car
  assert_func = form.car.value
  if assert_func == "=":
    lhs = rt.execute(rt.ns, form.cdr.car)
    rhs = rt.execute(rt.ns, form.cdr.cdr.car)
    return "%s != %s" % (repr(lhs), repr(rhs))
  if assert_func == "not":
    form = form.cdr.car
    if form.car.value == "=":
      lhs = rt.execute(rt.ns, form.cdr.car)
      rhs = rt.execute(rt.ns, form.cdr.cdr.car)
      return "%s == %s" % (repr(lhs), repr(rhs))
    return "%s != false" % repr(form)
  return repr(assert_func)

@pytest.mark.parametrize(("form"), forms)
def test_integration(form):
  try:
    if types.is_list(form) and types.is_symbol(form.car) and form.car.value == "is":
      result = rt.execute(rt.ns, form)
      assert types.true == result, "\nIn form:\n  %s\n\n%s" % (repr(form), pprint_assert(form))
    else:
      rt.execute(rt.ns, form)
  except LispException as e:
    assert False, "\nIn form:\n  %s\n\nException: %s" % (repr(form), e)
