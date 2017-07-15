package org.qrtt1.media;

import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;

public class MP4Parser {

    public MP4Parser(InputStream inputStream) {
        while (true) {
            Box box = readBox(inputStream);
            if (box == null) {
                break;
            }
            System.err.println(box);
            try {
                inputStream.skip(box.size);
            } catch (IOException e) {
                // TODO Auto-generated catch block
                e.printStackTrace();
            }
        }
    }

    public Box readBox(InputStream inputStream) {
        byte[] size = new byte[4];
        byte[] type = new byte[4];
        try {
            int r1 = inputStream.read(size);
            int r2 = inputStream.read(type);
            if (r1 == -1 || r2 == -1) {
                return null;
            }

            Box box = new Box();
            box.size = uint32beToInt(size, 0);
            box.type = new String(type);
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
            MP4Parser mp4Parser = new MP4Parser(input);
        }
    }
}
