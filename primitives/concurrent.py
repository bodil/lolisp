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

class Atom(types.Type):
  def __init__(self, value):
    types.Type.__init__(self, "atom", None)
    self.lock = threading.Lock()
    self.atom = value

  def __eq__(self, other):
    return self is other

  def swap(self, rt, scope, func):
    # FIXME: Lock should be acquired in request order
    self.lock.acquire()
    try:
      self.atom = rt.invoke(scope, func, [self.atom])
    except:
      import traceback
      traceback.print_exc()
    finally:
      rv = self.atom
      self.lock.release()
      return rv

  def deref(self):
    self.lock.acquire()
    rv = self.atom
    self.lock.release()
    return rv

  def __repr__(self):
    return "<atom=%s>" % repr(self.deref())

class LispWorker(threading.Thread):
  "Executes a series of forms in a separate thread."

  def __init__(self, rt, scope, forms):
    threading.Thread.__init__(self)
    self.rt = rt.clone()
    self.scope = scope
    self.forms = forms

  def done(self, result):
    raise NotImplementedError()

  def failed(self, exc):
    raise NotImplementedError()

  def run(self):
    rv = types.nil
    try:
      for form in self.forms:
        rv = self.rt.eval(self.scope, form)
      self.done(rv)
    except Exception as e:
      self.failed(e)

class Future(LispWorker):
  "Executes forms and realises a Ref with the result."

  def __init__(self, *args, **kwargs):
    LispWorker.__init__(self, *args, **kwargs)
    self.ref = Ref()

  def done(self, result):
    self.ref.realise(result)

  def failed(self, exc):
    self.ref.fail()

@extend("@Ref|Atom")
def deref(self, scope, args):
  ref = args[0]
  return ref.deref()

@extend("@any")
def atom(self, scope, args):
  return Atom(args[0])

@extend("swap!", "@Atom @callable")
def atom_swap(self, scope, args):
  return args[0].swap(self.rt, scope, args[1])

@extend("reset!", "@Atom @any")
def atom_reset(self, scope, args):
  fn = types.mkprimitive("reset!", lambda x1, x2: args[1])
  return args[0].swap(self.rt, scope, fn)

@extend("&")
def future(self, scope, args):
  f = Future(self.rt, scope, args[0])
  f.start()
  return f.ref

@extend("@number")
def sleep(self, scope, args):
  time.sleep(args[0].value)
  return types.nil
