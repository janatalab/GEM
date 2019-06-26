from threading import Thread
from time import time, sleep
import serial
import json
import re

# ==============================================================================
# convert a python int to a bytestring
def uint64(n):
    # make sure we add the bytes in low-high order (this has been tested
    # in one context but needs further testing)
    nstr = str()
    for k in range(0, 64, 8):
        nstr += chr((n >> k) & 0xff)
    return nstr
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
    def __init__(self, filepath, nrun):
        self.filepath = filepath

        self._io = open(filepath, "wb+")
        self.is_open = True
        self.ptr = 0

        # position in the file of the end of the last (run) header
        self.last_header_end = 0

        # position in the file of the start of the run header offset list
        self.idx_map_offset = 0

        # list start and end offsets for each run
        self.run_offsets = [-1] * nrun

        self.current_run = 0

    def close(self):
        if self.is_open:
            self.ptr = self._io.tell()
            self._io.close()
            self._io = None
            self.is_open = False

    def reopen(self):
        if not self.is_open:
            self._io = open(self.filepath, "r+b")
            self._io.seek(self.ptr, 0)
            self.is_open = True

    def write_header(self, krun, hdr_dict):
        self.reopen()
        if krun >= 0:
            if krun >= len(self.run_offsets):
                raise ValueError("\"%d\" is not a valid run number!" % krun)

            if self.run_offsets[krun] < 0:
                self.run_offsets[krun] = self._io.tell()
                self.write_run_offset(krun, self.run_offsets[krun])
            else:
                # the current run <krun> was previously aborted, so seek back
                # to where that run started to overwrite that run's data
                self._io.seek(self.run_offsets[krun], 0)

        hdr_str = json.dumps(hdr_dict)
        nel = len(hdr_str)

        # Write the length of the header dict as an 8 byte unsigned int
        self._io.write(uint64(nel))
        self._io.write(hdr_str)

    def write_file_header(self, d, nruns):
        self.reopen()
        self._io.seek(0, 0)
        self.write_header(-1, d)

        # initialize a block of run_header offsets with 64bit 0s
        print("Writing idx_map @ {}".format(self._io.tell()))
        self.idx_map_offset = self._io.tell()
        self._io.write('\x00' * 8 * nruns)

    def write_run_offset(self, krun, offset):
        self.reopen()
        ptr = self._io.tell()
        print("Writing run {} offset at: {}".format(krun, self.idx_map_offset + (krun * 8)))
        self._io.seek(self.idx_map_offset + (krun * 8), 0)
        self._io.write(uint64(offset))
        self._io.seek(ptr, 0)

# ==============================================================================
# class for debuging GEMIO systems w/o Arduino connection
class SerialSpoof:
    def __init__(self):
        self.in_waiting = 17
        self.x = 0

    def write(self, msg):
        foo = "Serial write: "
        for c in msg:
            foo += str(ord(c)) + ","
        print(foo)

    def read(self, n):
        sleep(0.4)
        return '\xff' + '\x01\x00' + '\x02\x00\x00\x00' + '\x03\x00' + '\x04\x00' + '\x05\x00' + '\x06\x00' + '\x07\x00'

    def readline(self):
        sleep(.050)

    def close(self):
        pass

    def isOpen(self):
        return True

# ==============================================================================
# GEMIO resource manager: allow for automatic resource clean up when used in
# a with statement
class GEMIOManager:
    # --------------------------------------------------------------------------
    def __init__(self, serial_ifo, datafile):
        self.ifo = serial_ifo
        self.datafile = datafile
    # --------------------------------------------------------------------------
    def __enter__(self):
        # ======================================================================
        # the actual GEMIO resource
        class GEMIOResource:
            def __init__(self, ifo, datafile):

                self.com = serial.Serial(
                    port=ifo["port"],
                    baudrate=ifo["baud_rate"],
                    timeout=ifo["timeout"]
                )

                # self.com = SerialSpoof()

                if self.com.isOpen():
                    print("serial is open!")

                self.file = datafile
                self.file.reopen()

            def close(self):
                self.com.close()
                self.file.close()

            def send(self, msg):
                self.com.write(msg)

            def flush(self):
                self.com.flush()

            def commit(self, n):
                self.file._io.write(self.com.read(n))

            def commit_debug(self, n):
                msg = self.com.read(n)
                self.file._io.write(msg)
                return msg

            def available(self):
                return self.com.in_waiting

        # ======================================================================

        self.io = GEMIOResource(self.ifo, self.datafile)

        return self.io
    # --------------------------------------------------------------------------
    def __exit__(self, err_type, err_value, traceback):
        self.io.close()

# ==============================================================================
#
class GEMAcquisition(Thread):
    def __init__(self, datafile, itc, presets, alpha):

        Thread.__init__(self)

        self.datafile = datafile
        self.itc = itc

        self.constants = parse_constants(presets["hfile"])
        self.serial_ifo = presets["serial"]
        self.run_duration = presets["run_duration"]

        self.windows = presets["windows"]

        self.tempo = self.constants["GEM_METRONOME_TEMPO"] + str(int(presets["metronome_tempo"]))

        self.alpha = self.constants["GEM_METRONOME_ALPHA"] + str(alpha)
        
        # add continuation related presets - LF 20190626
        self.prompt_windows = self.constants["GEM_METRONOME_PROMPT_WINDOWS"] + str(presets["metronome_prompt_windows"])
        
        self.stop_window = self.constants["GEM_METRONOME_STOP_WINDOW"] + str(presets["metronome_stop_window"])
        
        self.continuation = self.constants["GEM_METRONOME_CONTINUATION"] + str(presets["metronome_continuation"])

    # override Thread.run()
    def run(self):
        with GEMIOManager(self.serial_ifo, self.datafile) as io:

            # allow some time for handshake!
            io.com.readline()

            # send relevant parameters to arduino
            self.itc.send_message("data_viewer", "Sending tempo to arduino: " + self.tempo[1:])
            io.send(self.tempo)
            sleep(0.100)

            self.itc.send_message("data_viewer", "Sending alpha to arduino: " + self.alpha[1:])
            io.send(self.alpha)
            sleep(0.100)
            #
            # # TODO: wait for master to tell us it's ready?
            #

            # tell the master to start the experiment
            io.send(self.constants["GEM_STATE_RUN"])

            # notify anyone registered to receive GEM_START signals
            # no message is needed (defaults to "")
            self.itc.send_message("run_start")

            io.send(self.constants["GEM_START"])

            # track bytes received for debugging
            total = 0
            expected = 17 * self.windows #self.constants["GEM_PACKET_SIZE"] * self.windows

            tstart = time()
            done = self.itc.check_done()
            while (not done) and (total < expected):

                n = io.available()
                if n > 0:
                    io.commit(n)

                    # notify data viewer that we've received some data
                    self.itc.send_message("data_viewer", n)

                    # NOTE: echo incoming data to the data-viewer for debugging
                    # msg *SHOULD* be a byte-string... so I think we can just
                    # display as is in the data viewer
                    # msg = io.commit_debug(n)
                    # self.itc.send_message("data_viewer", msg)

                    # update byte count
                    total += n

                done = self.itc.check_done()

            io.send(self.constants["GEM_STOP"])

            print("[INFO]: Received {} bytes of data during this run".format(total))
            print("IO thread terminated")
