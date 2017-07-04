from threading import Thread
from time import time, sleep
import json
import serial

GEM_START = '\x01'
GEM_STOP = '\x00'

# ==============================================================================
# class to wrap common data file IO operations (writing headers etc.)
class GEMDataFile:
    def __init__(self, filepath):
        self.filepath = filepath

        # position in the file of the end of the last (run) header
        self.last_header_end = 0

        # position in the file of the start of the run header offset list
        self.header_offset = 0

        self.current_run = 0

    def uint64(self, n):
        # make sure we add the bytes in high-low order (this has been tested
        # in one context but needs further testing)
        nstr = str()
        inc = 7
        for k in range(0, 64, 8):
            nstr += chr((n >> k) & 0xff)
            inc -= 1
        return nstr

    def write_header(self, hdr_dict, write_offset = True):
        if write_offset:
            self.write_run_offset()

        hdr_str = json.dumps(hdr_dict)
        nel = len(hdr_str)

        with open(self.filepath, "ab") as io:
            # Write the length of the header dict as an 8 byte unsigned int
            io.write(self.uint64(nel))
            io.write(hdr_str)
            self.last_header_end = io.tell()

    def write_file_header(self, d, nruns):
        self.write_header(d, False)
        self.header_offset = self.last_header_end

        # initialize a block of run_header offsets with 64bit 0s
        with open(self.filepath, "ab") as io:
            zero64 = '\x00' * 8
            io.write(zero64 * nruns)
            self.last_header_end = io.tell()

    def write_run_offset(self):
        offset = 0
        with open(self.filepath, "ab") as io:
            io.seek(0, 2)
            offset = io.tell()
            io.seek(self.header_offset + (self.current_run * 8), 0)
            io.write(self.uint64(offset))

        self.current_run += 1

# ==============================================================================
# GEMIO resource manager: allow for automatic resource clean up when used in
# a with statement
class GEMIOManager:
    # --------------------------------------------------------------------------
    def __init__(self, serial_ifo, filepath):
        self.ifo = serial_ifo
        self.filepath = filepath
    # --------------------------------------------------------------------------
    def __enter__(self):
        # ======================================================================
        # the actual GEMIO resource
        class GEMIOResource:
            def __init__(self, ifo, filepath):
                self.com = serial.Serial(
                    ifo["port"],
                    ifo["baud_rate"],
                    ifo["timeout"]
                )

                self.file = open(filepath, "ab")

            def close(self):
                self.com.close()
                self.file.close()

            def send(self, msg):
                self.com.write(msg)

            def commit(self, n):
                self.file.write(self.com.read(n))

            def available(self):
                return self.com.in_waiting

        # ======================================================================

        self.io = GEMIOResource(self.ifo, self.filepath)

        return self.io
    # --------------------------------------------------------------------------
    def __exit__(self, err_type, err_value, traceback):
        self.io.close()

# ==============================================================================
#
class GEMAcquisition(Thread):
    def __init__(self, itc, filepath, presets):

        Thread.__init__(self)

        self.itc = itc
        self.serial_ifo = presets["serial"]
        self.filepath = filepath
        self.run_duration = presets["run_duration"]

    # override Thread.run()
    def run(self):
        with GEMIOManager(self.serial_ifo, self.filepath) as io:

            # tell the master to start the experiment
            io.send(GEM_START)

            tstart = time()
            while (not self.itc.check_done()) and (time() < (tstart + self.run_duration)):

                n = io.available()
                if n > 0:
                    # read into buffer

                    # interpret message header (need to assure only master sending in loop)
                        # have dict lookup table for how many bytes expecting

                        #pySerial Question: does other side know how many bytes arduino intended to send?

                    # parse message (write to formatted string)
                        # send str to text file and data viewer

                    # could add end of message signal (255)

                    # check length of byte stream and if end of message byte,
                        #if not raise error and end run?

                    io.commit(n)
                    # notify data viewer that we've received some data
                    self.itc.send_message(n)

                sleep(0.001)

            io.send(GEM_STOP)

            # call itc.done when laster window 
