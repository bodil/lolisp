var types = require("./types");
var sn = require("./ext/schemeNumber").SchemeNumber;
var _ = require("underscore");

module.exports = function math(rt) {
  var exports = {};

  var assert_signature = function assert_signature(fn, sig, args) {
    var i, l, arg, n, err = null;

    if (sig[0] === "&") {
      if (sig.length > 1) {
        i = parseInt(sig.slice(1), 10);
        if (args.length < i)
          throw "function " + fn + " takes at least " + i +
          "arguments, " + args.length + " given";
      }
      for (i = 0, l = args.length; i < l; i++) {
        arg = args[i];
        if (!types.is_number(arg))
          throw "function " + fn + " takes number as argument " +
          (i+1) + ", " + types.type_name(arg) + " given";
      }
      return;
    }

    if (args.length !== sig.length) {
      throw "function " + fn + " takes " + sig.length + " arguments, " +
        args.length + " given";
    }
    for (i = 0, l = args.length; i < l; i++) {
      arg = args[i];

      // *  any value
      // s  a string
      // z  any Scheme number
      // x  a real number
      // q  a rational number (excludes infinities and NaN)
      // n  an integer
      // k  an exact, non-negative integer

      if (sig[i] === "s" && !types.is_string(arg))
        err = "string";
      else if ("zxqnkrp".indexOf(sig[i]) >= 0) {
        n = arg.value;
        if (!types.is_number(arg))
          err = "number";
        else if (sig[i] === "x" && !sn.fn["real?"](n))
          err = "real number";
        else if (sig[i] === "q" && !sn.fn["rational?"](n))
          err = "rational number";
        else if (sig[i] === "n" && !sn.fn["integer?"](n))
          err = "integer";
        else if (sig[i] === "k" &&
                 (!sn.fn["integer?"](n) ||
                  sn.fn["negative?"](n) ||
                  !sn.fn["exact?"](n)))
          err = "exact non-negative integer";
      }

      if (err)
        throw "function " + fn + " takes " + err + " as argument " +
        (i+1) + ", " + types.type_name(arg) + " given";
    }
  };

  var def = function def(name, sig) {
    if (_.isArray(name)) {
      name.forEach(function(i) {
        def.apply(this, i);
      });
    } else {
      exports[name] = function(args) {
        args = args.map(rt.eval);
        assert_signature(name, sig, args);
        args = _.pluck(args, "value");
        return types.js_to_type(sn.fn[name].apply(this, args));
      };
    }
  };

  def([["integer?", "*"],
       ["real?", "*"],
       ["rational?", "*"],
       ["complex?", "*"],
       ["real-valued?", "*"],
       ["rational-valued?", "*"],
       ["integer-valued?", "*"],
       ["exact?", "z"],
       ["inexact?", "z"],
       ["inexact", "z"],
       ["exact", "z"],
       ["zero?", "z"],
       ["positive?", "x"],
       ["negative?", "x"],
       ["odd?", "n"],
       ["even?", "n"],
       ["finite?", "x"],
       ["infinite?", "x"],
       ["nan?", "x"],
       ["+", "&"],
       ["-", "&"],
       ["*", "&"],
       ["/", "&"],
       ["max", "&2"],
       ["min", "&2"],
       ["<", "&2"],
       [">", "&2"],
       ["<=", "&2"],
       [">=", "&2"],
       ["abs", "x"],
       ["div", "xx"],
       ["mod", "xx"],
       ["div-and-mod", "xx"],
       ["div0", "xx"],
       ["mod0", "xx"],
       ["div0-and-mod0", "xx"],
       ["gcd", "&"],
       ["lcm", "&"],
       ["numerator", "q"],
       ["denominator", "q"],
       ["floor", "x"],
       ["ceiling", "x"],
       ["truncate", "x"],
       ["round", "x"],
       ["rationalize", "xx"],
       ["exp", "z"],
       ["log", "&"],
       ["sin", "z"],
       ["cos", "z"],
       ["tan", "z"],
       ["asin", "z"],
       ["acos", "z"],
       ["atan", "&"],
       ["sqrt", "z"],
       ["exact-integer-sqrt", "k"],
       ["expt", "zz"],
       ["make-rectangular", "xx"],
       ["make-polar", "xx"],
       ["real-part", "z"],
       ["imag-part", "z"],
       ["magnitude", "z"],
       ["angle", "z"],
       ["string->number", "s"]
      ]);

  return exports;
};
