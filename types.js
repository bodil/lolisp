var types = {};

types.is_list = exports.is_list = function is_list(i) {
    return i instanceof Array && i.length;
};

types.is_atom = exports.is_atom = function is_atom(i) {
    return !types.is_list(i);
};

types.is_symbol = exports.is_symbol = function is_symbol(i) {
    return types.is_atom(i) && i.type === "symbol";
};

types.is_integer = exports.is_integer = function is_integer(i) {
    return types.is_atom(i) && i.type === "integer";
};

types.is_string = exports.is_string = function is_string(i) {
    return types.is_atom(i) && i.type === "string";
};

types.is_function = exports.is_function = function is_function(i) {
    return types.is_atom(i) && i.type === "function";
};

exports.is = function is(type , i) {
    return types["is_" + type](i);
};

exports.type_name = function type_name(i) {
    if (types.is_list(i)) return "list";
    if (types.is_symbol(i)) return "symbol";
    if (types.is_integer(i)) return "integer";
    if (types.is_string(i)) return "string";
    if (types.is_function(i)) return "function";
    return "unknown";
};

exports.mksymbol = function mksymbol(name) {
    return { type: "symbol", value: name};
};

exports.pprint = function pprint(s) {
    if (types.is_function(s))
        return "(lambda " + pprint(s.sig) + " " + s.value.map(pprint).join(" ") + ")";
    if (types.is_atom(s))
        return s.value;
    var out = [];
    for (var i = 0, l = s.length, el = s[0]; i < l; el = s[++i]) {
        out.push(pprint(el));
    }
    return "(" + out.join(" ") + ")";
};
