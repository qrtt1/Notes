# -*- encoding: utf-8 -*-
import struct

fname = "foo.mp4"
fname = "sample1.mp4"


def read_atom(data):
    """
        Read an atom and return a tuple of (size, type) where size is the size
        in bytes (including the 8 bytes already read) and type is a "fourcc"
        like "ftyp" or "moov".
    """
    size, type = struct.unpack(">L4s", data)
    type = type.decode('ascii')
    return size, type

# with open(fname, "rb") as fh:
# 
#     while True:
#         size, atom_type =  read_atom(fh.read(8))
#         data = fh.read(size - 8)
#         #print size, atom_type, data
#         print size, atom_type



# Press ENTER or type command to continue
# 24 ftyp
# 3195 free
# 1061109567 mdat
# Traceback (most recent call last):
#       File "r.py", line 20, in <module>

import StringIO

has_nested_atom = ['moov', 'trak', 'mdia', 'minf', 'stbl']

def load(parent, stream, result = []):
    header = stream.read(8)
    if len(header) == 0:
        raise StopIteration
    size, atom_type = read_atom(header)
    body = stream.read(size - 8)
    result += [(atom_type, size, parent, body)]
    if atom_type in has_nested_atom:
        load_all("%s%s." % (parent, atom_type), StringIO.StringIO(body), result)
    return result

def load_all(parent, stream, info):
    while True:
        try:
            load(parent, stream, info)
        except StopIteration:
            break

def dump_stts(stream):
    """
    http://www.52rd.com/blog/Detail_RD.Blog_wqyuwss_7920.html
    """
    version = stream.read(1)
    flag = stream.read(3)
    entries = stream.read(4)
    nb_entries = struct.unpack(">I", entries)[0]
    print "stts nb", nb_entries
    for e in range(nb_entries):
        count = stream.read(4)
        duration = stream.read(4)
        print "count", struct.unpack(">I", count)
        print "duration", struct.unpack(">I", duration)

def dump_stsd(stream):
    version = stream.read(1)
    flag = stream.read(3)
    entries = stream.read(4)
    nb_entries = struct.unpack(">I", entries)[0]
    for e in range(nb_entries):
        size = stream.read(4)
        fmt = stream.read(4)
        reserved = stream.read(6)
        ref = stream.read(2)
        print struct.unpack(">I", size)
        print struct.unpack(">I", fmt)

def int32(x):
    return struct.unpack(">I", x)[0]

def dump_stsz(stream):
    """
    http://www.52rd.com/blog/Detail_RD.Blog_wqyuwss_7924.html
    """
    version = stream.read(1)
    flag = stream.read(3)
    size = int32(stream.read(4))
    nb_entries = int32(stream.read(4))
    print "stsz nb", nb_entries
    for e in range(nb_entries):
        size = int32(stream.read(4))
        print "per sample size:", size

def as_stream(atom):
    return StringIO.StringIO(atom[3])


if __name__ == "__main__":

    info = []
    stream = open("foo.mp4", "rb")
    load_all(".", stream, info)

    for atom in [ x for x in info ]:
        print "%-30s" % atom[2], atom[:2]
        if atom[0] == "stsd": dump_stsd(as_stream(atom))
#        if atom[0] == "stts": dump_stts(as_stream(atom))
#        if atom[0] == "stsz": dump_stsz(as_stream(atom))


