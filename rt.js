var types = require("./types");
var primitives = require("./primitives");

module.exports = function rt() {
    var rt = {};

    rt.ns = {
        true: types.mksymbol("true"),
        false: types.mksymbol("false")
    };

    rt.scope = [ rt.ns ];

    /**
     * evaluate(exp):
     *
     * If exp is a list, exec it.
     * If exp is a symbol, resolve it.
     * Else, return it as is.
     */
    rt.eval = function eval(exp) {
        if (!types.is_atom(exp)) {
            return rt.exec(exp);
        } else if (types.is_symbol(exp)) {
            for (var i = rt.scope.length - 1; i >= 0; i--) {
                if (rt.scope[i][exp.value]) return rt.scope[i][exp.value];
            }
            if (rt.primitives[exp.value] !== undefined)
                return types.mkprimitive(exp.value);
            throw "name " + exp.value + " is undefined";
        } else return exp;
    };

    rt.invoke = function invoke(func, args) {
        var closure = {}, rv;

        if (args.length !== func.sig.length)
            throw types.type_name(func) + " takes " + func.sig.length + " arguments, " + args.length + " given";
        for (var i = 0, l = args.length; i < l; i++)
            closure[func.sig[i].value] = args[i];
        rt.scope.push(closure);
        for (i = 0, l = func.value.length; i < l; i++)
            rv = rt.exec(func.value[i]);
        rt.scope.pop();
        return rv;
    };

    rt.exec = function exec(list) {
        if (types.is_atom(list))
            return rt.eval(list);
        if (!list.length)
            return list;

        var func = list[0];
        var args = list.slice(1);

        if (types.is_symbol(func) && rt.primitives[func.value])
            return rt.primitives[func.value](args);

        func = rt.eval(func);

        if (types.is_macro(func)) {
            return rt.eval(rt.invoke(func, args));
        }

        if (types.is_function(func)) {
            return rt.invoke(func, args.map(rt.eval));
        }

        throw types.pprint(func) + " is not a function, it's a " + types.type_name(func);
    };

    rt.primitives = primitives(rt);

    return rt;
};
