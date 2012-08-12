import pytest
from lisptypes import *

def test_conj():
  l = cons(Type("number", 3), nil)
  l = cons(Type("number", 3), l)
  l = cons(Type("number", 1), l)
  l = cons(Type("number", 3), l)
  assert repr(l) == "(3 1 3 3)"
  assert repr(conj(l, Type("number", 7))) == "(3 1 3 3 7)"

def test_is_list():
  assert is_list(nil)
  assert is_list(cons(Type("number", 1337), nil))
  assert not is_list(Type("string", "ohai"))

def test_is_nil():
  assert is_nil(nil)
  assert not is_nil(Type("string", "ohai"))
  assert not is_nil(cons(Type("number", 1337), nil))

def test_is_atom():
  assert is_atomic(nil)
  assert is_atomic(Type("string", "ohai"))
  assert not is_atomic(cons(Type("number", 1337), nil))
  assert not is_atomic("ohai")

def test_type_name():
  assert type_name(Type("string", "ohai")) == "string"
  assert type_name(nil) == "nil"
  assert type_name(cons(Type("string", "ohai"), nil)) == "list"

def test_mksymbol():
  assert is_symbol(mksymbol("ohai"))
  assert mksymbol("ohai").value == "ohai"

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
