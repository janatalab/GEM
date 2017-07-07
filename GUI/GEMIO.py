from threading import Thread
from time import time, sleep
import json
import serial
import re

# ==============================================================================
# parse a string containing a c/c++ uinsigned int literal
def parse_uint(val):
    #uint -> char, all other data type can stay as strings
    if val[0:2] == "0x":
        v = val[2:].decode("hex")
    else:
        v = val
    return v

# ==============================================================================
# remove c/c++ style comments from a string
def remove_comments(src):
    pattern = re.compile(r"(?:/\*(?:[^*]|(?:\*+[^*/]))*\*+/)|(?://.*)")
    return pattern.sub("", src)

# ==============================================================================
# parse preprocessor defines from a .h file
# in: <hfile> the path to the header file to parse
# out: a dictionary mapping define names to values (strings)
def parse_constants(hfile):
    with open(hfile, "r") as io:
        src = remove_comments(io.read())

    d = dict()
    pattern = re.compile(r"\#define\s+(?P<name>\w+)\s+(?P<val>\w+)")
    for match in pattern.finditer(src):
        d[match.group("name")] = parse_uint(match.group("val"))

    return d

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

            #def buffer(self, msg):
                # buffer incoming bytes until we have the number expected given
                # the dtp (then send)
                # TODO

            #def parse_message(self, protocol, msg):
                # parse the msg, given its dtp (expected byte length)
                # TODO

            def send(self, msg):
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

        self.hfile = presets["hfile"]
        self.constants = parse_constants(self.hfile)
        print(self.constants)
        self.itc = itc
        self.serial_ifo = presets["serial"]
        self.filepath = filepath
        self.run_duration = presets["run_duration"]
        self.tempo = int(presets["metronome_tempo"])
        self.tempo = self.constants["GEM_METRONOME_TEMPO"] + str(self.tempo)
        self.currAlpha = self.constants["GEM_METRONOME_ALPHA"] + str(presets["currAlpha"])

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
            io.send(self.constants["GEM_STATE_RUN"])
            io.send(self.constants["GEM_START"])

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

            io.send(self.constants["GEM_STOP"])
