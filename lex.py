from shlex import shlex
import re

class ParserError(Exception):
  def __init__(self, value, token = None):
    self.value = value
    self.token = token
  def __str__(self):
    if self.token:
      return "%s:%d: %s" % (self.token["infile"],
                            self.token["lineno"],
                            self.value)
    return self.value

classifiers = (
  ("lparen", re.compile(r"\(")),
  ("rparen", re.compile(r"\)")),
  ("string", re.compile(r"\".*")),
  ("quote", re.compile(r"'")),
  ("unquote", re.compile(r"~")),
  ("deref", re.compile(r"@")),
  ("number", re.compile(r"[1-9-]*[0-9][0-9./]*")),
  ("symbol", re.compile(r"[a-zA-Z_+*/=<>&|?!.-][a-zA-Z0-9_+*/=<>&|?!.-]*")),
)

def classify(token):
  for (t, r) in classifiers:
    if r.match(token):
      return t
  raise ParserError("Unclassifiable token \"%s\"" % token)

class Lexer(object):
  def __init__(self, stream, filename = None):
    if not filename and isinstance(stream, file):
      filename = stream.name
    l = shlex(stream, filename, posix = False)
    l.commenters = ";"
    l.wordchars = l.wordchars + "+-*/=<>&|?.!"
    l.whitespace = ", \t\r\n"
    l.escape = "\\"
    l.quotes = "\""
    self.lexer = l

  def __iter__(self):
    for token in self.lexer:
      yield { "type": classify(token),
              "value": token,
              "lineno": self.lexer.lineno,
              "infile": self.lexer.infile }
