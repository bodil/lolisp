var types = require("./types");
var _ = require("underscore");

var assert_signature = function assert_signature(fn, args) {
    var sig = Array.apply(null, arguments).slice(2);
    if (args.length !== sig.length) {
        throw "function " + fn + " takes " + sig.length + " arguments, " +
            args.length + " given";
    }
    for (var i = 0, l = args.length; i < l; i++) {
        if (sig[i] !== "*" && !types.is(sig[i], args[i])) {
            console.log(args[i]);
            throw "function " + fn + " takes " + sig[i] + " as argument " +
                (i+1) + ", " + types.type_name(args[i]) + " given";
        }
    }
};

module.exports = function primitives(rt) {
    return {
        "quote": function(args) {
            assert_signature("quote", args, "*");
            return args[0];
        },

        "define": function(args) {
            assert_signature("define", args, "symbol", "*");
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
            if (types.is_atom(list))
                throw "argument 2 of cons must resolve to a list, but is " + list.type;
            return [ cons ].concat(list);
        },

        "car": function(args) {
            assert_signature("car", args, "*");
            var list = rt.eval(args[0]);
            if (types.is_atom(list))
                throw "argument 1 of car must resolve to a list, but is " + list.type;
            return (list.length) ? list[0] : [];
        },

        "cdr": function(args) {
            assert_signature("cdr", args, "*");
            var list = rt.eval(args[0]);
            if (types.is_atom(list))
                throw "argument 1 of cdr must resolve to a list, but is " + list.type;
            return (list.length) ? list.slice(1) : [];
        },

        "cond": function(args) {
            var test, rv;
            for (var i = 0, l = args.length, arg = args[i]; i < l; arg = args[++i]) {
                if (types.is_atom(arg))
                    throw "argument " + (i+1) + " of cond should be a list, is " + arg.type;
                if (arg.length < 2)
                    throw "argument " + (i+1) + " of cond must have a length of >=2, is " + arg.length;
            }
            for (i = 0, l = args.length, arg = args[i]; i < l; arg = args[++i]) {
                test = rt.eval(arg[0]);
                if (!types.is_symbol(test) || (test.value !== "true" && test.value !== "false"))
                    throw "expr " + types.pprint(arg[0]) + " does not rt.eval to a boolean";
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
            if (types.is_atom(sig))
                throw "argument 1 of lambda must be list, is " + types.type_name(sig);
            for (var i = 0, l = sig.length, arg = sig[i]; i < l; arg = sig[++i])
                if (!types.is_symbol(arg))
                    throw "argument 1 of lambda must be a list of symbols, but element " +
                i + " is " + types.type_name(arg);
            return { type: "function", sig: sig, value: body };
        },

        "print": function (args) {
            args = args.map(rt.eval);
            console.log.apply(null, args.map(types.pprint));
            return [];
        }
    };
};
