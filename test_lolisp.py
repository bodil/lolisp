import pytest, sys, os.path, glob
import lisptypes as types
from errors import LispException
from load import load
from rt import RT

test_files = glob.glob(os.path.join(sys.path[0], "test-loli", "*.loli"))

def build_rt(filename):
  rt = RT()
  rt.__test_filename__ = filename
  rt.load(rt.ns, file(os.path.join(sys.path[0], "rt.loli")))
  rt.ns.define("is", types.mkprimitive("is", lambda s, a: rt.eval(s, a[0])))
  return rt

def pytest_generate_tests(metafunc):
  args = []
  for f in test_files:
    rt = build_rt(os.path.basename(f))
    for form in load(file(f)):
      args.append((rt, form))
  metafunc.parametrize(metafunc.funcargnames, args)

def pprint_assert(rt, form):
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

def test_integration(rt, form):
  try:
    if types.is_list(form) and types.is_symbol(form.car) and form.car.value == "is":
      result = rt.execute(rt.ns, form)
      assert types.true == result, "\nIn file %s:\nIn form:\n  %s\n\n%s" % (rt.__test_filename__, repr(form), pprint_assert(rt, form))
    else:
      rt.execute(rt.ns, form)
  except LispException as e:
    pytest.fail("\nIn file %s:\nIn form:\n  %s\n\nException: %s" % (rt.__test_filename__, repr(form), e))
