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

  def fail(self):
    self.realise(False)

  def realised(self):
    self.condition.acquire()
    rv = not self.refval is None
    self.condition.release()
    return rv

  def failed(self):
    self.condition.acquire()
    rv = self.refval is False
    self.condition.release()
    return rv

  def deref(self):
    self.condition.acquire()
    if self.refval == None:
      self.condition.wait()
    rv = self.refval
    self.condition.release()
    if rv is False:
      return types.mksymbol("failed")
    return rv

  def __repr__(self):
    if self.realised():
      return "<ref=%s>" % repr(self.deref())
    else:
      return "<ref=unrealised>"

@extend("@Ref")
def deref(self, scope, args):
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
    try:
      for form in self.forms:
        print "Exec:", form
        rv = self.rt.eval(form)
      self.ref.realise(rv)
    except LispException:
      import traceback
      traceback.print_exc()
      self.ref.realise(types.nil)

@extend("&")
def future(self, scope, args):
  f = FutureWorker(self.rt, args[0])
  f.start()
  return f.ref

@extend("@number")
def sleep(self, scope, args):
  time.sleep(args[0].value)
  return types.nil
