"""
Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of them are required to have default values!
"""

import numpy as np
from gnuradio import gr
from collections import deque
from enum import Enum
import pmt

chip = [
    1618456172, 1309113062, 1826650030, 1724778362, 778887287, 2061946375,
    2007919840, 125494990,  529027475,  838370585,  320833617, 422705285,
    1368596360, 85537272,   139563807,  2021988657
    ];

class DecoderState(Enum):
    PREAMBLE_SEARCH = 1
    PREAMBLE_GET = 2
    SFD_GET = 3
    PHR_GET = 4
    PSDU_GET = 5
    ERROR = 100

debug_enabled = 0

def debug(msg, **kwargs):
    if debug_enabled == 1:
        print(msg, kwargs)

class blk(gr.sync_block):  # other base classes are basic_block, decim_block, interp_block
    """Embedded Python Block example - a simple multiply const"""

    def __init__(self):  # only default arguments here
        """arguments to this function show up as parameters in GRC"""
        gr.sync_block.__init__(
            self,
            name='Zigbee FM Decoder',   # will show up in GRC
            in_sig=[np.byte],
            out_sig=[]
        )
        # type should be faster, lets see
        self.val = np.uint32(0)
        # initial precalculations
        for i in range(0,len(chip)):
            chip[i] = chip[i] & 0x7FFFFFFE
        self.state = DecoderState.PREAMBLE_SEARCH;
        self.bits_processed = 0
        self.bits_to_fetch = 1
        self.threshold = 5
        self.chip_found = -1

        self.message_port_register_out(pmt.intern('pdu_out'))

    def work(self, input_items, output_items):
        for i in input_items[0]:
            self.val = self.val << 1
            self.val = self.val | i
            self.bits_processed += 1
            if (self.bits_processed == self.bits_to_fetch):
                self.bits_processed = 0;
                for i in range(0,len(chip)):
                    res = ((self.val & 0x7FFFFFFE) ^ chip[i]).bit_count()
                    if res < self.threshold:
                        # chip found
                        chip_val = i
                        break;
                    else:
                        chip_val = -1
                    # we only intrested in checking 0 for preamble,
                    # no need for additional chip check
                    if self.state == DecoderState.PREAMBLE_SEARCH:
                        break

                if self.state == DecoderState.PREAMBLE_SEARCH:
                    if chip_val == 0:
                        print("Synced to preamble and found preamble chip")
                        self.bits_to_fetch = 32
                        self.state = DecoderState.PREAMBLE_GET
                        self.preamble_chips = 1;
                elif self.state == DecoderState.PREAMBLE_GET:
                    debug("Found next preamble chip")
                    if chip_val == 0:
                        self.preamble_chips += 1
                        if (self.preamble_chips == 8):
                            debug("All chips found")
                            self.state = DecoderState.SFD_GET
                            self.symbol_no = 0
                            self.data = []
                    else:
                        print("Preamble error")
                        self.state = DecoderState.ERROR
                elif self.state == DecoderState.SFD_GET:
                    if chip_val != -1:
                        debug("found chip {}".format(chip_val));
                        self.data.append(chip_val)
                        self.symbol_no += 1;
                        if (self.symbol_no == 2):
                            val = self.data[1] << 4 | self.data[0];
                            debug("found SFD {}".format(hex(val)));
                            if (val == 0xA7):
                                self.symbol_no = 0;
                                self.data = [];
                                self.state = DecoderState.PHR_GET;
                            else:
                                print("SFD val error");
                                self.state = DecoderState.ERROR
                    else:
                        print("SFD error")
                        self.state = DecoderState.ERROR
                elif self.state == DecoderState.PHR_GET:
                    if chip_val != -1:
                        debug("found chip {}".format(chip_val));
                        self.data.append(chip_val)
                        self.symbol_no += 1;
                        if (self.symbol_no == 2):
                            val = self.data[1] << 4 | self.data[0];
                            debug("found PHR {}".format(hex(val)));
                            # symbol contains 4 bits we need to
                            # multiply by 2 to fetch all data
                            self.psdu_len = val * 2
                            self.data = []
                            self.symbol_no = 0
                            self.state = DecoderState.PSDU_GET
                    else:
                        print("PHR error")
                        self.state = DecoderState.ERROR
                elif self.state == DecoderState.PSDU_GET:
                    if chip_val != -1:
                        debug("found chip {}".format(chip_val));
                        self.data.append(chip_val)
                        self.symbol_no += 1;
                        if (self.symbol_no == self.psdu_len):
                            psdu = []
                            for i in range(0,len(self.data),2):
                                psdu.append(self.data[i+1] << 4 | self.data[i+0])
                            debug("PSDU ", end="")
                            print(list(map(hex, psdu)))
                            msg = pmt.cons(pmt.PMT_NIL, pmt.init_u8vector(len(psdu), psdu))
                            self.message_port_pub(pmt.intern("pdu_out"), msg);
                            self.data = []
                            self.state = DecoderState.PREAMBLE_SEARCH
                            self.bits_to_fetch = 1;
                            self.val = 0;
                    else:
                        print("PSDU error")
                        self.state = DecoderState.ERROR
                elif self.state == DecoderState.ERROR:
                    self.data = []
                    self.state = DecoderState.PREAMBLE_SEARCH
                    self.bits_to_fetch = 1;



        return len(input_items[0])
