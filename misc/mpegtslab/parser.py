import struct
import StringIO

filename = "WebLive_BBC_1_360p_256k.mp40.ts"


def byte(x):
    return struct.unpack("B", x)[0]

def binstr(x):
    return format(byte(x), "08b")

class Bits(object):

    def __init__(self, binary_data):
        self.stream = StringIO.StringIO(binary_data)

    def read(self, num_bits):
        data = self.stream.read(num_bits)
        return int(data, 2)

    def read_byte(self):
        return struct.pack("B", self.read(8))

    def read_hex(self, message, num_bits):
        value = self.read(num_bits)
        print "%s: 0x%x" % (message, value)
        return value

    def read_int(self, message, num_bits):
        value = self.read(num_bits)
        print "%s: %d" % (message, value)
        return value

    def read_binstr(self, message, num_bits):
        data = self.stream.read(num_bits)
        print "%s: %s" % (message, data)
        return data

    def check_finish(self):
        data = self.stream.read()
        if len(data) != 0:
            raise ValueError("data not consumed, remaining %d" % (len(data)))



class TransportPacket(object):

    def __init__(self, data):
        self.data = data
        print self.parse_header()

    def parse_header(self):
        bits = self.read_header()

        # sync_byte 8 bslbf
        self.sync_byte = bits.read_hex("sync_byte", 8)
        # transport_error_indicator 1 bslbf
        self.transport_error_indicator = bits.read_int("transport_error_indicator", 1)
        # payload_unit_start_indicator 1 bslbf
        self.payload_unit_start_indicator = bits.read_int("payload_unit_start_indicator", 1)
        # transport_priority 1 bslbf
        self.transport_priority = bits.read_int("transport_priority", 1)
        # PID 13 uimsbf
        self.PID = bits.read_hex("PID", 13)
        # transport_scrambling_control 2 bslbf
        self.transport_scrambling_control = bits.read_int("transport_scrambling_control", 2)
        # adaptation_field_control 2 bslbf
        self.adaptation_field_control = bits.read_binstr("adaptation_field_control", 2)
        # continuity_counter 4 uimsbf
        self.continuity_counter = bits.read_int("continuity_counter", 4)
        bits.check_finish()

        self.next_start_index = 4
        self.adaptation_field_length = 0

        if self.adaptation_field_control == "10" or self.adaptation_field_control == "11":
            self.adaptation_field_length = byte(self.data[4])
            self.next_start_index = self.next_start_index + self.adaptation_field_length
            self.parse_adaptation_field()

    def parse_adaptation_field(self):
        data = []
        for x in range(4, 4 + self.adaptation_field_length):
            data.append(binstr(self.data[x]))
        bits = Bits("".join(data))

        length = bits.read_int("adaptation_field_length", 8)
        if length != self.adaptation_field_length:
            raise ValueError("adaptation_field_length is not same with upstreaming parser")

        if length == 1:
            return

        self.adaptation_field = {}
        # discontinuity_indicator 1 bslbf
        self.adaptation_field['discontinuity_indicator'] = bits.read_int("af:discontinuity_indicator", 1)
        # random_access_indicator 1 bslbf
        self.adaptation_field['random_access_indicator'] = bits.read_int("af:random_access_indicator", 1)
        # elementary_stream_priority_indicator 1 bslbf
        self.adaptation_field['elementary_stream_priority_indicator'] = bits.read_int("af:elementary_stream_priority_indicator", 1)
        # PCR_flag 1 bslbf
        self.adaptation_field['PCR_flag'] = bits.read_int("af:PCR_flag", 1)
        # OPCR_flag 1 bslbf
        self.adaptation_field['OPCR_flag'] = bits.read_int("af:OPCR_flag", 1)
        # splicing_point_flag 1 bslbf
        self.adaptation_field['splicing_point_flag'] = bits.read_int("af:splicing_point_flag", 1)
        # transport_private_data_flag 1 bslbf
        self.adaptation_field['transport_private_data_flag'] = bits.read_int("af:transport_private_data_flag", 1)
        # adaptation_field_extension_flag 1 bslbf
        self.adaptation_field['adaptation_field_extension_flag'] = bits.read_int("af:adaptation_field_extension_flag", 1)

        # if (PCR_flag == '1') {
        #     program_clock_reference_base 33 uimsbf
        #     reserved 6 bslbf
        #     program_clock_reference_extension 9 uimsbf
        # }
        if self.adaptation_field['PCR_flag']:
            self.adaptation_field['PCR'] = {}
            self.adaptation_field['PCR']['program_clock_reference_base'] = bits.read_int("af:PCR:program_clock_reference_base", 33)
            bits.read(6)
            self.adaptation_field['PCR']['program_clock_reference_extension'] = bits.read_int("af:PCR:program_clock_reference_extension", 9)

        # if (OPCR_flag == '1') {
        #     original_program_clock_reference_base 33 uimsbf
        #     reserved 6 bslbf
        #     original_program_clock_reference_extension 9 uimsbf
        # }
        if self.adaptation_field['OPCR_flag']:
            self.adaptation_field['OPCR'] = {}
            self.adaptation_field['OPCR']['original_program_clock_reference_base'] = bits.read_int("af:OPCR:original_program_clock_reference_base", 33)
            bits.read(6)
            self.adaptation_field['OPCR']['original_program_clock_reference_extension'] = bits.read_int("af:OPCR:original_program_clock_reference_extension", 9)

        # if (splicing_point_flag = = '1') {
        #     splice_countdown 8 tcimsbf
        # }
        if self.adaptation_field['splicing_point_flag']:
            self.adaptation_field['splice_countdown'] = bits.read_int("af:splice_countdown", 8)


        # if (transport_private_data_flag = = '1') {
        #     transport_private_data_length 8 uimsbf
        #     for (i = 0; i < transport_private_data_length; i++) {
        #         private_data_byte 8 bslbf
        #     }
        # }
        if self.adaptation_field['transport_private_data_flag']:
            self.adaptation_field['transport_private_data'] = {}
            self.adaptation_field['transport_private_data']['transport_private_data_length'] = bits.read_int("transport_private_data_length", 8)
            self.adaptation_field['transport_private_data']['private_data_byte'] = []
            for x in range(self.adaptation_field['transport_private_data']['transport_private_data_length']):
                self.adaptation_field['transport_private_data']['private_data_byte'].append(bits.read_byte())


    def read_header(self):
        data = []
        for x in range(4):
            data.append(binstr(self.data[x]))
        return Bits("".join(data))


    def _read_data_bytes(self):
        packet_start_code_prefix = self.binstrs(self.data[4:7])
        print packet_start_code_prefix


    def binstrs(self, d = []):
        values = []
        for x in d:
            values.append(self.binstr(x))
        return "".join(values)
#

with open(filename) as fh:
    count = 100000
    count = 40
    while count > 0:
        count = count - 1

        packet = fh.read(188)
        if len(packet) == 0:
            break
        TransportPacket(packet)


