var _ = require("underscore");
var SchemeNumber = require("./ext/schemeNumber").SchemeNumber;

var types = {};

types.is_list = exports.is_list = function is_list(i) {
  return i instanceof Array;
};

types.is_nil = exports.is_nil = function is_nil(i) {
  return types.is_list(i) && i.length === 0;
};

types.is_atom = exports.is_atom = function is_atom(i) {
  return types.is_nil(i) || !types.is_list(i);
};

types.is_symbol = exports.is_symbol = function is_symbol(i) {
  return types.is_atom(i) && i.type === "symbol";
};

types.is_number = exports.is_number = function is_number(i) {
  return types.is_atom(i) && i.type === "number";
};

types.is_string = exports.is_string = function is_string(i) {
  return types.is_atom(i) && i.type === "string";
};

types.is_function = exports.is_function = function is_function(i) {
  return types.is_atom(i) && i.type === "function";
};

types.is_primitive = exports.is_primitive = function is_function(i) {
  return types.is_atom(i) && i.type === "primitive";
};

types.is_macro = exports.is_macro = function is_macro(i) {
  return types.is_atom(i) && i.type === "macro";
};

exports.is = function is(type , i) {
  return types["is_" + type](i);
};

exports.type_name = function type_name(i) {
  if (types.is_nil(i)) return "nil";
  if (types.is_list(i)) return "list";
  if (types.is_symbol(i)) return "symbol";
  if (types.is_number(i)) return "number";
  if (types.is_string(i)) return "string";
  if (types.is_function(i)) return "function";
  if (types.is_primitive(i)) return "primitive";
  if (types.is_macro(i)) return "macro";
  return "unknown";
};

exports.token_to_type = function token_to_type(token) {
  var type = _.clone(token);
  if (type.type === "string") {
    type.value = token.value.slice(1, token.value.length - 1);
  } else if (type.type === "number") {
    type.value = SchemeNumber.fn["string->number"](type.value);
  }
  return type;
};

exports.mksymbol = function mksymbol(name) {
  return { type: "symbol", value: name };
};

exports.mkprimitive = function mkprimitive(name) {
  return { type: "primitive", value: name };
};

exports.js_to_type = function js_to_type(obj) {
  if (obj === true)
    return exports.mksymbol("true");
  if (obj === false)
    return exports.mksymbol("false");
  if (_.isString(obj))
    return { type: "string", value: obj };
  if (SchemeNumber.fn["number?"](obj))
    return { type: "number", value: obj };
  if (_.isNumber(obj))
    return { type: "number", value: new SchemeNumber(obj) };
  if (_.isArray(obj)) {
    return obj.map(js_to_type);
  }
  throw "object " + obj + " cannot be converted to a type";
};

exports.pprint = function pprint(s) {
  if (types.is_macro(s))
    return "<macro " + pprint(s.sig) + " " + s.value.map(pprint).join(" ") + ">";
  if (types.is_function(s))
    return "(lambda " + pprint(s.sig) + " " + s.value.map(pprint).join(" ") + ")";
  if (types.is_primitive(s))
    return "<primitive " + s.value + ">";
  if (types.is_number(s))
    return SchemeNumber.fn["number->string"](s.value);
  if (types.is_string(s))
    return '"' + s.value + '"';
  if (types.is_nil(s))
    return "()";
  if (types.is_atom(s))
    return s.value;
  var out = [];
  for (var i = 0, l = s.length, el = s[0]; i < l; el = s[++i]) {
    out.push(pprint(el));
  }
  return "(" + out.join(" ") + ")";
};
