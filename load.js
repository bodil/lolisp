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
                tmp = [ types.mksymbol("quote"), tmp.slice(1) ];
            top.push(tmp);
            break;
        default:
            top.push((last.type === "quote")
                     ? [ types.mksymbol("quote"), token ]
                     : token);
            break;
        }
        last = token;
    }
    if (top !== root) throw "UNBALANCED PARENTHESES LOL@U";
    return root;
};
