import struct



filename = "WebLive_BBC_1_360p_256k.mp40.ts"

class TransportPacket(object):

    def __init__(self, data):
        self.data = data
        self._read_header()

    def _read_header(self):
        # sync_byte 8 bslbf
        self.sync_byte = self.binstr(self.data[0])

        # transport_error_indicator 1 bslbf
        # payload_unit_start_indicator 1 bslbf
        # transport_priority 1 bslbf
        data = self.binstr(self.data[1]) + self.binstr(self.data[2])

        self.transport_error_indicator = data[0]
        self.payload_unit_start_indicator = data[1]
        self.transport_priority = data[2]

        # PID 13 uimsbf
        self.PID = "0x%04x" % int(data[3:], 2)


        # transport_scrambling_control 2 bslbf
        # adaptation_field_control 2 bslbf
        # continuity_counter 4 uimsbf
        data = self.binstr(self.data[3])
        self.transport_scrambling_control = data[:2]
        self.adaptation_field_control = data[2:4]
        self.continuity_counter = data[4:]

        print "adaptation_field_control", self.adaptation_field_control
        print "payload_unit_start_indicator", self.payload_unit_start_indicator
        print "PID", self.PID
        if self.adaptation_field_control == "10" or self.adaptation_field_control == "11":
            print "should process adaptation_field"
            pass

        if self.adaptation_field_control == "01" or self.adaptation_field_control == "11":
#            if self.payload_unit_start_indicator == "1":
#                self._read_data_bytes()
            pass



    def _read_data_bytes(self):
        packet_start_code_prefix = self.binstrs(self.data[4:7])
        print packet_start_code_prefix

    def byte(self, d):
        return struct.unpack("B", d)[0]

    def binstr(self, d):
        return format(self.byte(d), "08b")

    def binstrs(self, d = []):
        values = []
        for x in d:
            values.append(self.binstr(x))
        return "".join(values)
#

with open(filename) as fh:
    count = 100000
    count = 4
    while count > 0:
        count = count - 1

        packet = fh.read(188)
        if len(packet) == 0:
            break
        TransportPacket(packet)


