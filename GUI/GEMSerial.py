from threading import Thread
from time import sleep
import serial

tmp_port = "/dev/cu.usbmodem1421"
PACKET_LENGTH = 13
# ==============================================================================
# GEMIO resource manager: allow for automatic resource clean up when used in
# a with statement
class GEMIOResource:
    # --------------------------------------------------------------------------
    def __init__(self, serial_ifo, filepath):
        self.ifo = serial_ifo
        self.filepath = filepath
    # --------------------------------------------------------------------------
    def __enter__(self):
        # ======================================================================
        # the actual GEMIO resource
        class GEMIO:
            def __init__(self, ifo, filepath):
                self.n = 0

                self.com = serial.Serial(
                    ifo["com_port"],
                    ifo["baud_rate"],
                    ifo["timeout"]
                )

                self.file = open(filepath, "a")

            def close(self):
                self.com.close()
                self.file.close()

            def send(self, msg):
                self.com.write(msg)

            def commit(self, n):
                self.file.write(self.com.read(n))

            def wait(self):
                while self.com.in_waiting < 1:
                    sleep(0.001)

                n = self.com.in_waiting
                self.commit(n)

                self.n += n

                return self.n

            def reset(self):
                self.n = 0
        # ======================================================================

        self.io = GEMIO(self.ifo, self.filepath)

        return self.io
    # --------------------------------------------------------------------------
    def __exit__(self, err_type, err_value, traceback):
        self.io.close()

# ==============================================================================
#
class GEMAcquisition(Thread):
    def __init__(self, itc, presets, filepath):
        self.itc = itc
        self.ifo = presets["serial"]
        self.filepath = filepath
        self.windows = presets["windows"]

    # override Thread.run()
    def run(self):
        with GEMIOResource(self.ifo, self.filepath) as io

            # tell the master to start the experiment
            io.send(GEM_START)

            kwindow = 0
            done = self.itc.check_done()
            while (not done) && (kwindow < self.windows):

                # wait until a byte(s) is(are) available from the serial driver
                # dump byte(s) to the data file
                # once we have 13 bytes notify the data viewer that we've successfully
                # received a packet (increment window counter etc.)
                while (io.wait() < PACKET_LENGTH) && (not done):
                    done = self.itc.check_done()

                if not done:
                    # notify data viewer that we've received a full packet and reset
                    # io's byte count
                    self.itc.send_message(io.n)
                    io.reset()

                    kwindow += 1

                    done = self.itc.check_done()

            io.send(GEM_STOP)
