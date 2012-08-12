class LispException(Exception):
  def __init__(self, value, symbol = None):
    self.value = value
    self.symbol = symbol
  def __str__(self):
    if self.symbol and hasattr(self.symbol, "token"):
      return "%s:%d: %s" % (self.symbol.token.infile,
                            self.symbol.token.lineno,
                            self.value)
    return self.value
