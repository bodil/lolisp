var fs = require("fs");
var types = require("./types");
var load = require("./load");
var rt = require("./rt")();

var argv = require("optimist").check(function(argv) {
  if (argv._.length > 1) throw "One file at a time!";
}).usage("Run you a lisp!\nUsage: $0 [source-file]").argv;

if (argv._.length > 0) {
  var ast = load(fs.readFileSync(argv._[0], "utf-8"));
  for (var i = 0, l = ast.length, stm = ast[0]; i < l; stm = ast[++i]) {
    try {
      rt.exec(stm);
    } catch (e) {
      process.stdout.write("*** In form: " + types.pprint(stm) +
                           "\n*** " + e + "\n");
      process.exit(1);
    }
  }
  process.exit(0);
}

process.stdout.write(">>> ");
process.stdin.resume();
process.stdin.setEncoding('utf8');

process.stdin.on('data', function repl(s) {
  try {
    var ast = load(s);
    for (var i = 0, l = ast.length, stm = ast[0]; i < l; stm = ast[++i]) {
      console.log(" => " + types.pprint(rt.exec(stm)));
    }
    process.stdout.write(">>> ");
  } catch (e) {
    process.stdout.write("*** " + e + "\n>>> ");
  }
});

process.stdin.on('end', function end() {
  process.stdout.write("\n");
  process.exit(0);
});
