var types = require("./types");
var load = require("./load");
var rt = require("./rt")();

if (!rt.loadFile(__dirname + "/rt.loli")) process.exit(1);

var argv = require("optimist").check(function(argv) {
  if (argv._.length > 1) throw "One file at a time!";
}).usage("Run you a lisp!\nUsage: $0 [source-file]").argv;

if (argv._.length > 0) {
  process.exit(rt.loadFile(argv._[0]) ? 0 : 1);
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
