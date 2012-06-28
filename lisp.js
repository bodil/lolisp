var Lexer = require("./lexer");
var _ = require("underscore");

var grammar = {
    symbol: { regexp: /^[a-zA-Z_+*/=-]+[a-zA-Z0-9_+*/=|-]*$/, skip: false },
    string: { regexp: /^\"[^\"]*\"$/, skip: false },
    integer: { regexp: /^[1-9]*\d+$/, skip: false },
    quote: { regexp: /^'$/, skip: false },
    lparen: { regexp: /^\($/, skip: false },
    rparen: { regexp: /^\)$/, skip: false },
    whitespace: { regexp: /^[\t \n,]$/, skip: true }
};

var lex = function(s) {
    var lexer = new Lexer(s, grammar);
    var stream = [];
    while (!lexer.eof) {
        lexer.next();
        if (lexer.token === "string") lexer.lexeme = lexer.lexeme.slice(1, lexer.lexeme.length - 1);
        stream.push({ type: lexer.token, value: lexer.lexeme });
    }
    return stream;
};

var is_list = function(i) { return i instanceof Array && i.length; };
var is_atom = function(i) { return !is_list(i); };
var is_symbol = function(i) { return is_atom(i) && i.type === "symbol"; };
var is_integer = function(i) { return is_atom(i) && i.type === "integer"; };
var is_string = function(i) { return is_atom(i) && i.type === "string"; };
var is_function = function(i) { return is_atom(i) && i.type === "function"; };
var is = function(type, i) { return eval("is_" + type)(i); };
var type_name = function(i) {
    if (is_list(i)) return "list";
    if (is_symbol(i)) return "symbol";
    if (is_integer(i)) return "integer";
    if (is_string(i)) return "string";
    if (is_function(i)) return "function";
    return "unknown";
};

var mksymbol = function(name) { return { type: "symbol", value: name }; };

var load = function(s) {
    var root = [];
    var stack = [root];
    var top = root;
    var tmp, last = {};

    for (var i = 0, l = s.length, token = s[0]; i < l; token = s[++i]) {
        switch (token.type) {
        case "EOF":
            i = l;
            break;
        case "quote":
            break;
        case "lparen":
            top = (last.type === "quote") ? ["quote"] : [];
            stack.push(top);
            break;
        case "rparen":
            if (stack.length == 1) throw "UNBALANCED PARENTHESES LOL@U";
            tmp = top;
            stack.pop();
            top = stack[stack.length - 1];
            if (tmp[0] === "quote")
                tmp = [ mksymbol("quote"), tmp.slice(1) ];
            top.push(tmp);
            break;
        default:
            top.push((last.type === "quote")
                     ? [ mksymbol("quote"), token ]
                     : token);
            break;
        }
        last = token;
    }
    if (top !== root) throw "UNBALANCED PARENTHESES LOL@U";
    return root;
};

var pprint = function(s) {
    if (is_function(s))
        return "(lambda " + pprint(s.sig) + " " + s.value.map(pprint).join(" ") + ")";
    if (is_atom(s))
        return s.value;
    var out = [];
    for (var i = 0, l = s.length, el = s[0]; i < l; el = s[++i]) {
        out.push(pprint(el));
    }
    return "(" + out.join(" ") + ")";
};

var assert_signature = function(fn, args) {
    var sig = Array.apply(null, arguments).slice(2);
    if (args.length !== sig.length) {
        throw "function " + fn + " takes " + sig.length + " arguments, " +
            args.length + " given";
    }
    for (var i = 0, l = args.length; i < l; i++) {
        if (sig[i] !== "*" && !is(sig[i], args[i])) {
            throw "function " + fn + " takes " + sig[i] + " as argument " +
                (i+1) + ", " + type_name(args[i]) + " given";
        }
    }
};

var ns = {
    true: mksymbol("true"),
    false: mksymbol("false")
};

var scope = [ ns ];

/**
 * evaluate(exp):
 *
 * If exp is a list, exec it.
 * If exp is a symbol, resolve it.
 * Else, return it as is.
 */
var evaluate = function(exp) {
    if (is_list(exp)) {
        return exec(exp);
    } else if (is_symbol(exp)) {
        for (var i = scope.length - 1; i >= 0; i--) {
            if (scope[i][exp.value]) return scope[i][exp.value];
        }
        throw "name " + exp.value + " is undefined";
    } else return exp;
};

var primitives = {
    "quote": function(args) {
        assert_signature("quote", args, "*");
        return args[0];
    },
    "define": function(args) {
        assert_signature("define", args, "symbol", "*");
        return ns[args[0].value] = evaluate(args[1]);
    },
    "=": function(args) {
        assert_signature("=", args, "*", "*");
        args = args.map(evaluate);
        return _.isEqual(args[0], args[1]) ? ns.true : ns.false;
    },
    "atom": function(args) {
        assert_signature("atom", args, "*");
        return (is_atom(evaluate(args[0]))) ? ns.true : ns.false;
    },
    "cons": function(args) {
        assert_signature("cons", args, "*", "*");
        var cons = evaluate(args[0]);
        var list = evaluate(args[1]);
        if (is_atom(list))
            throw "argument 2 of cons must resolve to a list, but is " + list.type;
        return [ cons ].concat(list);
    },
    "car": function(args) {
        assert_signature("car", args, "*");
        var list = evaluate(args[0]);
        if (is_atom(list))
            throw "argument 1 of car must resolve to a list, but is " + list.type;
        return (list.length) ? list[0] : [];
    },
    "cdr": function(args) {
        assert_signature("cdr", args, "*");
        var list = evaluate(args[0]);
        if (is_atom(list))
            throw "argument 1 of cdr must resolve to a list, but is " + list.type;
        return (list.length) ? list.slice(1) : [];
    },
    "cond": function(args) {
        var test, rv;
        for (var i = 0, l = args.length, arg = args[i]; i < l; arg = args[++i]) {
            if (is_atom(arg))
                throw "argument " + (i+1) + " of cond should be a list, is " + arg.type;
            if (arg.length < 2)
                throw "argument " + (i+1) + " of cond must have a length of >=2, is " + arg.length;
        }
        for (i = 0, l = args.length, arg = args[i]; i < l; arg = args[++i]) {
            test = evaluate(arg[0]);
            if (!is_symbol(test) || (test.value !== "true" && test.value !== "false"))
                throw "expr " + pprint(arg[0]) + " does not evaluate to a boolean";
            if (test.value === "true") {
                for (var j = 1, m = arg.length, stm = arg[j]; j < m; stm = arg[++j]) {
                    rv = evaluate(stm);
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
        if (is_atom(sig))
            throw "argument 1 of lambda must be list, is " + type_name(sig);
        for (var i = 0, l = sig.length, arg = sig[i]; i < l; arg = sig[++i])
            if (!is_symbol(arg))
                throw "argument 1 of lambda must be a list of symbols, but element " +
                i + " is " + type_name(arg);
        return { type: "function", sig: sig, value: body };
    },
    "print": function (args) {
        args = args.map(evaluate);
        console.log.apply(null, args.map(pprint));
        return [];
    },
    "load": function (args) {
        assert_signature("load", args, "*");
        var val = evaluate(args[0]);
        if (!is_string(val)) throw "load takes a string argument, " + val.type + " given";
        return load(lex(val.value))[0];
    }
};

var exec = function(list) {
    if (is_atom(list))
        return evaluate(list);
    if (!list.length)
        return list;

    var func = list[0];
    var args = list.slice(1);
    var closure = {}, rv;

    if (is_symbol(func) && primitives[func.value])
        return primitives[func.value](args);

    func = evaluate(func);

    if (is_function(func)) {
        if (args.length !== func.sig.length)
            throw "function takes " + func.sig.length + " arguments, " + args.length + " given";
        args = args.map(evaluate);
        for (var i = 0, l = args.length; i < l; i++)
            closure[func.sig[i].value] = args[i];
        scope.push(closure);
        for (i = 0, l = func.value.length; i < l; i++)
            rv = exec(func.value[i]);
        scope.pop();
        return rv;
    }

    throw pprint(func) + " is not a function, it's a " + type_name(func);
};

var repl_exec = function(s) {
    try {
        var ast = load(lex(s));
        for (var i = 0, l = ast.length, stm = ast[0]; i < l; stm = ast[++i]) {
            console.log(" => " + pprint(exec(stm)));
        }
        process.stdout.write(">>> ");
    } catch (e) {
        process.stdout.write("*** " + e + "\n>>> ");
    }
};

process.stdout.write(">>> ");
process.stdin.resume();
process.stdin.setEncoding('utf8');

process.stdin.on('data', function (s) {
    repl_exec(s);
});

process.stdin.on('end', function () {
    process.stdout.write("\n");
    process.exit(0);
});
