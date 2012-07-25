var lex = require("./lex");
var types = require("./types");

module.exports = function load(s) {
    var root = [];
    var stack = [root];
    var top = root;
    var tmp, last = {};

    s = lex(s);

    for (var i = 0, l = s.length, token = s[0]; i < l; token = s[++i]) {
        switch (token.type) {
        case "EOF":
            i = l;
            break;
        case "quote":
        case "unquote":
            break;
        case "lparen":
            if (last.type === "quote") top = ["quote"];
            else if (last.type === "unquote") top = ["unquote"];
            else top = [];
            stack.push(top);
            break;
        case "rparen":
            if (stack.length == 1) throw "UNBALANCED PARENTHESES LOL@U";
            tmp = top;
            stack.pop();
            top = stack[stack.length - 1];
            if (tmp[0] === "quote")
                tmp = [ types.mksymbol("quote"), tmp.slice(1) ];
            else if (tmp[0] === "unquote")
                tmp = [ types.mksymbol("unquote"), tmp.slice(1) ];
            top.push(tmp);
            break;
        default:
            if (last.type === "quote") {
                top.push([types.mksymbol("quote"), types.token_to_type(token)]);
            } else if (last.type === "unquote") {
                top.push([types.mksymbol("unquote"), types.token_to_type(token)]);
            } else {
                top.push(types.token_to_type(token));
            }
            break;
        }
        last = token;
    }
    if (top !== root) throw "UNBALANCED PARENTHESES LOL@U";
    return root;
};
