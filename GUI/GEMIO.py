from threading import Thread
from time import time, sleep
import serial
import json
import re
import codecs, struct

import serial.tools.list_ports


# ==============================================================================
# convert a python int to a bytestring
def uint64(n):
    return n.to_bytes(8,byteorder='little')

# ==============================================================================
# parse a string containing a c/c++ uinsigned int literal
def parse_uint(val):
    #uint -> char, all other data type can stay as strings
    if val[0:2] == "0x":
        v = codecs.decode(val[2:],"hex")
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
# Function to get the relevant USB port
#
# Define a unique identifier for the usb device used to connect the metronome
# Arduino. This could be something like "Arduino", though on our UC Davis
# GEM system, we use a usb adapter from the Arduino to the computer that has an
# ID of "Generic CDC".

def get_metronome_port(usb_adapter="Generic CDC", serial_num=None):
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        # If we've specified the serial number we are looking for, use that
        if serial_num:
            m = re.search(r'SER='+serial_num, p.hwid)
            if m:
                return p.device

        else:
            # Check for ID of usb adapter we use to connect Arduino
            if usb_adapter in p[1]:
                pid = str(p)
                return pid.split(' ')[0]


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
        nel_uint64 = uint64(nel)

        # Write the length of the header dict as an 8 byte unsigned int
        self._io.write(nel_uint64) 

        # Write the header
        hdr_offset = self._io.tell()
        print(f"Writing header of length {nel} ({nel_uint64}) at {hdr_offset}: \n{hdr_str}")
        self._io.write(hdr_str.encode())

    def write_file_header(self, d, nruns):
        self.reopen()
        self._io.seek(0, 0)
        self.write_header(-1, d)

        # initialize a block of run_header offsets with 64bit 0s
        self.idx_map_offset = self._io.tell()
        print("Writing idx_map @ {}".format(self.idx_map_offset))
        
        self._io.write(bytes(8*nruns))

    def write_run_offset(self, krun, offset):
        self.reopen()
        ptr = self._io.tell()
        print("Writing run {} offset ({}) at: {}".format(krun+1, offset, self.idx_map_offset + (krun * 8)))
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
    def __init__(self, serial_ifo, datafile, is_spoof):
        self.ifo = serial_ifo
        self.datafile = datafile
        self.is_spoof = is_spoof
    # --------------------------------------------------------------------------
    def __enter__(self):
        # ======================================================================
        # the actual GEMIO resource
        class GEMIOResource:
            def __init__(self, ifo, datafile, is_spoof):

                if not is_spoof:
                    self.com = serial.Serial(
                        port=ifo["port"],
                        baudrate=ifo["baud_rate"],
                        timeout=ifo["timeout"]
                    )

                else:
                    self.com = SerialSpoof()

                if self.com.isOpen():
                    print("serial is open!")

                self.file = datafile
                self.file.reopen()

            def close(self):
                self.com.close()
                self.file.close()

            def send(self, msg):
                self.com.write(msg)
                print(f"Sent {msg}")

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

        self.io = GEMIOResource(self.ifo, self.datafile, self.is_spoof)

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

        self.tempo = self.constants["GEM_METRONOME_TEMPO"] + bytes(str(int(presets["metronome_tempo"])), 'utf-8') 

        self.alpha = self.constants["GEM_METRONOME_ALPHA"] + bytes(str(alpha),'utf-8')

        self.is_spoof = presets.get("spoof_mode", False)


        self.is_spoof = presets.get("spoof_mode", False)

        self.sounds = self.constants["GEM_SOUNDS"] + str(presets["sound_ids"])

    # override Thread.run()
    def run(self):
        with GEMIOManager(self.serial_ifo, self.datafile, self.is_spoof) as io:

            # allow some time for handshake!
            io.com.readline()

            # send relevant parameters to arduino
            self.itc.send_message("data_viewer", "Sending tempo to arduino: " + self.tempo[1:].decode('utf-8'))
            io.send(self.tempo)
            sleep(0.100)

            self.itc.send_message("data_viewer", "Sending alpha to arduino: " + self.alpha[1:].decode('utf-8'))
            io.send(self.alpha)
            sleep(0.100)

            #
            # # TODO: wait for metronome to tell us it's ready
            #

            # tell the metronome to start the experiment
            io.send(self.constants["GEM_STATE_RUN"])

            # notify anyone registered to receive GEM_START signals
            # no message is needed (defaults to "")
            self.itc.send_message("run_start")
            io.send(self.constants["GEM_START"])

            # track bytes received for debugging
            total = 0
            expected = int(self.constants["GEM_PACKET_SIZE"]) * self.windows

            print(f"[INFO]: Expecting {expected} bytes total")

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
                    # print(f"[INFO]: {total} bytes received so far")

                # Check for an abort
                done = self.itc.check_done()

            io.send(self.constants["GEM_STOP"])

            print(f"[INFO]: Received {total} bytes of data during this run")
            print("IO thread terminated")
