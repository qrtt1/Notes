package org.qrtt1.media;

import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.ArrayList;
import java.util.List;

public class MP4Parser {

    List<Box> boxes = new ArrayList<>();

    public void parse(InputStream inputStream, Box parent) {
        long offset = 0;
        while (true) {
            Box box = readBox(inputStream, parent);
            if (box == null) {
                break;
            }
            box.start = offset;
            box.end = box.start + box.size;
            offset += box.size;
            boxes.add(box);
            if (box.hasChildren()) {
                parse(inputStream, box);
            }

            System.out.println(box);
        }
    }

    private Box readBox(InputStream inputStream, Box parent) {
        byte[] size = new byte[4];
        byte[] type = new byte[4];
        try {
            int r1 = inputStream.read(size);
            int r2 = inputStream.read(type);
            if (r1 == -1 || r2 == -1) {
                return null;
            }

            Box box = new Box();
            box.parent = parent;
            box.size = uint32beToInt(size, 0);
            box.type = new String(type);

            if (!box.hasChildren()) {
                inputStream.skip(box.size - 8);
            }
            return box;
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    public static long uint32beToInt(byte[] data, int offset) {
        ByteBuffer buf = ByteBuffer.allocate(8).put(new byte[] { 0, 0, 0, 0 }).put(data).order(ByteOrder.BIG_ENDIAN);
        buf.position(0);
        return buf.getLong();
    }

    public static void main(String[] args) throws FileNotFoundException, IOException {
        try (InputStream input = new FileInputStream("/Users/qrtt1/Desktop/sample.mp4")) {
            // input.skip(2237327872L);
            MP4Parser mp4Parser = new MP4Parser();
            mp4Parser.parse(input, null);
        }
    }
}
