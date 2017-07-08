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
            while (not self.signal) && (not self.end):
                self.cv.wait()

            if not self.end:
                # if <to> is a signal (i.e. has listeners) then call all
                # callbacks that have registered with that signal, otherwise,
                # if <to> has a registered queue add the msg to the queue
                if self.signal in self.listeners:
                    for receiver in self.listeners[self.signal]:
                        receiver(self.buffer)
                elif self.signal in self.queue:
                    self.queue[self.signal].appendleft(self.buffer)

                self.signal = ""
                self.buffer = ""
            else:
                done = True

            self.cv.release()
    # --------------------------------------------------------------------------
    # full scale abort: kill message waiting, send done to IO thread
    def close(self):
        self.cv.acquire()
        self.end = True
        self.cv.notify_all()
        self.cv.release()

        # send terminate message to IO thread
        self.done()

        # wait until our dispatch thread ends (should have already ended)
        self.join()

        # all resources are cleaned up, ok to close app
        return True

    # --------------------------------------------------------------------------
    # register a callback for named signals
    def register_listener(self, signal, callback):
        if not signal in self.listeners:
            self.listeners[signal] = list()

        self.listeners[signal] = callback

    # --------------------------------------------------------------------------
    # send a message to all entities that have registered with the name <to>
    def send_message(self, to, msg=""):
        self.cv.acquire()
        self.signal = to
        self.buffer = msg
        self.cv.notify()
        self.cv.release()

    # --------------------------------------------------------------------------
    # toggle the isdone state to true: effectivly tell IO thread to end
    def done(self):
        self.done_lock.acquire()
        self.isdone = True
        self.done_lock.release()

    # --------------------------------------------------------------------------
    # check the state of the isdone flag
    def check_done(self):
        self.done_lock.acquire()
        ret = self.isdone
        self.done_lock.release()
        return ret
