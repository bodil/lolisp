import pytest
from primitives import *

def signature_fixture():
  from rt import RT
  rt = RT()
  prims = Primitives(rt)
  invoke = lambda func, args: func(prims, rt.ns, args)
  invoke.rt = rt
  return invoke

def test_signature_passthrough():
  invoke = signature_fixture()
  @signature("*")
  def passthrough(self, scope, args):
    assert args == ["foo", "bar"]
  invoke(passthrough, ["foo", "bar"])

def test_signature_type_checking():
  invoke = signature_fixture()
  @signature("string number")
  def type_check(self, scope, args):
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
  def resolve_arg(self, scope, args):
    assert types.is_nil(args[0])
  invoke(resolve_arg, [types.mksymbol("nil")])
  with pytest.raises(LispException):
    invoke(resolve_arg, [types.mksymbol("not-defined")])

def test_signature_rest_argument():
  invoke = signature_fixture()
  @signature("any &")
  def rest(self, scope, args):
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
  def rest(self, scope, args):
    assert len(args) == 2
    assert types.is_nil(args[0])
    assert isinstance(args[1], list)
    assert args[1] == list(types.py_to_type([13, 37]))
  invoke(rest, [types.nil, types.mksymbol("ohai"),
                types.mksymbol("noobs")])
  with pytest.raises(LispException):
    invoke(rest, [types.nil, types.mksymbol("not-defined")])
