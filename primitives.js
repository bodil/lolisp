var types = require("./types");
var load = require("./load");
var math = require("./math");
var _ = require("underscore");

var assert_signature = function assert_signature(fn, args) {
  var sig = Array.apply(null, arguments).slice(2);
  if (args.length !== sig.length) {
    throw "function " + fn + " takes " + sig.length + " arguments, " +
      args.length + " given";
  }
  for (var i = 0, l = args.length; i < l; i++) {
    if (sig[i] !== "*" && !types.is(sig[i], args[i])) {
      throw "function " + fn + " takes " + sig[i] + " as argument " +
        (i+1) + ", " + types.type_name(args[i]) + " given";
    }
  }
};

module.exports = function primitives(rt) {

  var is_splice = function is_splice(v) {
    return !types.is_nil(v) && types.is_list(v) &&
      types.is_symbol(v[0]) && v[0].value == "unquote-splice";
  };

  var unquote = function unquote(v) {
    if (!types.is_nil(v) && types.is_list(v)) {
      if (types.is_symbol(v[0]) && v[0].value == "unquote")
        return rt.eval(v[1]);
      var i, it, out = [];
      for (i = 0, it = v[0]; i < v.length; it = v[++i]) {
        if (is_splice(it)) {
          out = out.concat(rt.eval(it[1]));
        } else out.push(unquote(it));
      }
      return out;
    } else return v;
  };

  var p = {
    "quote": function(args) {
      assert_signature("quote", args, "*");
      return unquote(args[0]);
    },

    "unquote": function(args) {
      assert_signature("unquote", args, "*");
      return rt.eval(args[0]);
    },

    "unquote-splice": function() {
      throw "you can't use unquote-splice outside of quote";
    },

    "define": function(args) {
      assert_signature("define", args, "symbol", "*");
      if (rt.primitives[args[0].value] !== undefined)
        throw "defining symbol " + args[0].value +
        " would override a primitive";
      return rt.ns[args[0].value] = rt.eval(args[1]);
    },

    "=": function(args) {
      assert_signature("=", args, "*", "*");
      args = args.map(rt.eval);
      return _.isEqual(args[0], args[1]) ? rt.ns.true : rt.ns.false;
    },

    "atom": function(args) {
      assert_signature("atom", args, "*");
      return (types.is_atom(rt.eval(args[0]))) ? rt.ns.true : rt.ns.false;
    },

    "cons": function(args) {
      assert_signature("cons", args, "*", "*");
      var cons = rt.eval(args[0]);
      var list = rt.eval(args[1]);
      if (types.is_list(list))
        return [cons].concat(list);
      if (types.is_string(list)) {
        if (!types.is_string(cons))
          throw "you can only cons strings onto strings, but argument 1 of cons is " + cons.type;
        return types.js_to_type(cons.value + list.value);
      }
      throw "argument 2 of cons must resolve to a list or a string, but is " + list.type;
    },

    "car": function(args) {
      assert_signature("car", args, "*");
      var list = rt.eval(args[0]);
      if (types.is_list(list))
        return (list.length) ? list[0] : [];
      if (types.is_string(list))
        return types.js_to_type(list.value[0]);
      throw "argument 1 of car must resolve to a list or a string, but is " + list.type;
    },

    "cdr": function(args) {
      assert_signature("cdr", args, "*");
      var list = rt.eval(args[0]);
      if (types.is_list(list))
        return (list.length) ? list.slice(1) : [];
      if (types.is_string(list))
        return types.js_to_type(list.value.slice(1));
      throw "argument 1 of cdr must resolve to a list or a string, but is " + list.type;
    },

    "cond": function(args) {
      var test, rv;
      for (var i = 0, l = args.length, arg = args[i]; i < l; arg = args[++i]) {
        if (!types.is_list(arg))
          throw "argument " + (i+1) + " of cond should be a list, is " + arg.type;
        if (arg.length < 2)
          throw "argument " + (i+1) + " of cond must have a length of >=2, is " + arg.length;
      }
      for (i = 0, l = args.length, arg = args[i]; i < l; arg = args[++i]) {
        test = rt.eval(arg[0]);
        if (!types.is_symbol(test) || (test.value !== "true" && test.value !== "false"))
          throw "expr " + types.pprint(arg[0]) + " does not evaluate to a boolean";
        if (test.value === "true") {
          for (var j = 1, m = arg.length, stm = arg[j]; j < m; stm = arg[++j]) {
            rv = rt.eval(stm);
          }
          return rv;
        }
      }
      return [];
    },

    "lambda": function(args) {
      if (args.length < 2)
        throw "lambda takes at least 2 arguments, " + args.length + " given";
      var sig = args[0], body = args.slice(1);
      if (!types.is_list(sig))
        throw "argument 1 of lambda must be list, is " + types.type_name(sig);
      for (var i = 0, l = sig.length, arg = sig[i]; i < l; arg = sig[++i])
        if (!types.is_symbol(arg))
          throw "argument 1 of lambda must be a list of symbols, but element " +
        i + " is " + types.type_name(arg);
      return { type: "function", sig: sig, value: body };
    },

    "print": function(args) {
      args = args.map(rt.eval);
      console.log.apply(null, args.map(function(i) {
        return types.is_string(i) ? i.value : types.pprint(i);
      }));
      return [];
    },

    "load": function(args) {
      assert_signature("load", args, "*");
      var val = rt.eval(args[0]);
      if (!types.is_string(val))
        throw "load takes a string argument, " + val.type + " given";
      return load(val.value)[0];
    },

    "eval": function(args) {
      assert_signature("eval", args, "*");
      return rt.eval(rt.eval(args[0]));
    },

    "not": function(args) {
      assert_signature("not", args, "*");
      var val = rt.eval(args[0]);
      if (!types.is_symbol(val) || (val.value !== "true" && val.value !== "false"))
        throw "expr " + types.pprint(args[0]) + " does not evaluate to a boolean";
      return (val.value === "true") ? rt.ns.false : rt.ns.true;
    },

    "macro": function(args) {
      if (args.length < 2)
        throw "defmacro takes at least 2 arguments, " + args.length + " given";
      var sig = args[0], body = args.slice(1);
      if (!types.is_list(sig))
        throw "argument 1 of defmacro must be list, is " + types.type_name(sig);
      for (var i = 0, l = sig.length, arg = sig[i]; i < l; arg = sig[++i])
        if (!types.is_symbol(arg))
          throw "argument 1 of defmacro must be a list of symbols, but element " +
        i + " is " + types.type_name(arg);

      return { type: "macro", sig: sig, value: body};
    },

    "apply": function(args) {
      assert_signature("apply", args, "*", "*");
      args = args.map(rt.eval);
      if (!types.is_list(args[1]))
        throw "argument 2 of apply must resolve to a list, is " + types.type_name(args[1]);
      return rt.eval([args[0]].concat(args[1]));
    },

    "foldr": function(args) {
      assert_signature("foldr", args, "*", "*", "*");
      args = args.map(rt.eval);
      if (!types.is_list(args[2]))
        throw "argument 3 of foldr must resolve to a list, is " + types.type_name(args[2]);
      var i, l = args[2], len = l.length, acc = args[1];
      for (i = 0; i < len; i++) {
        acc = rt.invoke(args[0], [acc, l[i]]);
      }
      return acc;
    },

    "foldl": function(args) {
      assert_signature("foldl", args, "*", "*", "*");
      args = args.map(rt.eval);
      if (!types.is_list(args[2]))
        throw "argument 3 of foldl must resolve to a list, is " + types.type_name(args[2]);
      var i, l = args[2], acc = args[1];
      for (i = l.length - 1; i >= 0; i--) {
        acc = rt.invoke(args[0], [acc, l[i]]);
      }
      return acc;
    },

    "load-file": function(args) {
      assert_signature("load-file", args, "*");
      args = args.map(rt.eval);
      if (!types.is_string(args[0]))
        throw "argument 1 of load-file must resolve to a string, is " + types.type_name(args[2]);
      return rt.loadFile(args[0].value) ? rt.ns.true : rt.ns.false;
    }
  };

  _.extend(p, math(rt));
  return p;
};
