import lisptypes as types
from errors import LispException
from primitives import extend
import threading, time

class Ref(types.Type):
  def __init__(self):
    types.Type.__init__(self, "ref", None)
    self.refval = None
    self.condition = threading.Condition()

  def __eq__(self, other):
    return self is other

  def realise(self, value):
    self.condition.acquire()
    self.refval = value
    self.condition.notifyAll()
    self.condition.release()

  def realised(self):
    self.condition.acquire()
    rv = not self.refval == None
    self.condition.release()
    return rv

  def deref(self):
    self.condition.acquire()
    if self.refval == None:
      self.condition.wait()
    rv = self.refval
    self.condition.release()
    return rv

  def __repr__(self):
    if self.realised():
      return "<ref=%s>" % repr(self.deref())
    else:
      return "<ref=unrealised>"

@extend("@Ref")
def deref(self, args):
  ref = args[0]
  return ref.deref()

class FutureWorker(threading.Thread):
  def __init__(self, rt, forms):
    threading.Thread.__init__(self)
    self.rt = rt.clone()
    self.ref = Ref()
    self.forms = forms

  def run(self):
    rv = types.nil
    for form in self.forms:
      rv = self.rt.eval(form)
    self.ref.realise(rv)

@extend("&")
def future(self, args):
  f = FutureWorker(self.rt, args[0])
  f.start()
  return f.ref

@extend("@number")
def sleep(self, args):
  time.sleep(args[0].value)
  return types.nil
