from threading import Thread
from time import time, sleep
import json
import serial

# would like to import GEMConstants.h instead. Look into h2py - LF 20170703
GEM_START = '\x01'
GEM_STOP = '\x00'
GEM_STATE_RUN = '\x04' #4

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
                print(ifo)
                self.com = serial.Serial(
                    port=ifo["port"],
                    baudrate=ifo["baud_rate"],
                    timeout=ifo["timeout"]
                )

                if self.com.isOpen():
                    print("serial is open!")

                self.file = open(filepath, "ab")

            def close(self):
                self.com.close()
                self.file.close()

            def send(self, msg):
                # if isinstance(msg, int):
                #     # convert int to binary
                #     msg = '{0:08b}'.format(msg)
                #     print("sending %d to arduino" % int(msg,2))
                #     self.com.write(msg)
                # else:
                print("sending %d to arduino" % ord(msg[0]))
                self.com.write(msg)

            def flush(self):
                self.com.flush()

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
        self.tempo = int(presets["metronome_tempo"])
        # TODO: get these string vals from constants file
        self.tempo = '\x12' + str(self.tempo)
        self.currAlpha = '\x17' + str(presets["currAlpha"])

    # override Thread.run()
    def run(self):
        with GEMIOManager(self.serial_ifo, self.filepath) as io:

            # allow some time for handshake!
            io.com.readline()

            # send relevant parameters to arduino
            print("sending tempo to arduino...")
            print(self.tempo)
            io.send(self.tempo)
            sleep(1)

            print("sending this run's alpha value to arduino...")
            print(self.currAlpha)
            io.send(self.currAlpha)
            sleep(1)
            #
            # # TODO: wait for master to tell us it's ready?
            #

            # tell the master to start the experiment
            io.send(GEM_STATE_RUN)
            io.send(GEM_START)

            tstart = time()
            done = self.itc.check_done()
            while (not done) and (time() < (tstart + self.run_duration)):

                n = io.available()
                if n > 0:
                    io.commit(n)

                    # notify data viewer that we've received some data
                    self.itc.send_message(n)
                    print("Sending to itc: %d" % n)

                done = self.itc.check_done()
                io.com.flushOutput()

            io.send(GEM_STOP)
