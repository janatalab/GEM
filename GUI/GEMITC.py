from threading import Thread, Lock, Condition
from collections import deque

# ==============================================================================
# Inter-thread-communicator
class ITC(Thread):
    # --------------------------------------------------------------------------
    def __init__(self):

        Thread.__init__(self)

        # lock for <isdone>
        self.done_lock = Lock()

        # single purpose flag for sending bool "finish" message to the IO thread
        self.isdone = False

        # condition var for messages and master end flag
        self.cv = Condition()

        self.listener_lock = Lock()

        # dict mapping recipient names to callback function for immediate
        # processing upon receiving a message
        self.listeners = dict()

        # buffers to hold the most recent message and signal/recipient name
        self.buffer = ""
        self.signal = ""

        # master flag set by close() to abort and message waiting that is
        # happening when it's time to close the application
        self.end = False

    # --------------------------------------------------------------------------
    def run(self):
        done = False
        while not done:
            self.cv.acquire()

            # wait until a message is available or someone called close()
            while (not self.signal) and (not self.end):
                self.cv.wait()

            if not self.end:
                self.listener_lock.acquire()

                # if <to> is a signal (i.e. has listeners) then call all
                # callbacks that have registered with that signal, otherwise,
                # if <to> has a registered queue add the msg to the queue
                if self.signal in self.listeners:
                    for receiver in self.listeners[self.signal]:
                        # print("sending signal: %s, msg: %s" % (self.signal, str(self.buffer)))
                        receiver(self.buffer)

                self.listener_lock.release()

                self.signal = ""
                self.buffer = ""
            else:
                done = True
                print("ITC thread received close")

            self.cv.release()
        print("ITC thread terminated")
    # --------------------------------------------------------------------------
    # full scale abort: kill message waiting, send done to IO thread
    def close(self):
        print("Closing ITC resources...")
        self.cv.acquire()
        self.end = True
        self.cv.notify_all()
        self.cv.release()

        # send terminate message to IO thread
        self.set_done(True)

        # wait until our dispatch thread ends (should have already ended)
        self.join()

        # all resources are cleaned up, ok to close app
        return True

    # --------------------------------------------------------------------------
    # register a callback for named signals
    def register_listener(self, signal, callback):
        print("registering listener for signal: " + signal)
        self.listener_lock.acquire()
        if not signal in self.listeners:
            self.listeners[signal] = list()

        self.listeners[signal].append(callback)
        self.listener_lock.release()

    # --------------------------------------------------------------------------
    # send a message to all entities that have registered with the name <to>
    def send_message(self, to, msg=""):
        self.cv.acquire()
        # print("buffering signal: %s, msg: %s " % (to, str(msg)))
        self.signal = to
        self.buffer = msg
        self.cv.notify()
        self.cv.release()

    # --------------------------------------------------------------------------
    # toggle the isdone state to true: effectivly tell IO thread to end
    def set_done(self, val=True):
        self.done_lock.acquire()
        self.isdone = val
        self.done_lock.release()

    # --------------------------------------------------------------------------
    # check the state of the isdone flag
    def check_done(self):
        self.done_lock.acquire()
        ret = self.isdone
        self.done_lock.release()
        return ret
