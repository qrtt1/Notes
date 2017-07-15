package org.qrtt1.media;

public class Box {

    long size;
    String type;
    Box parent;
    Box child;

    @Override
    public String toString() {
        return "Box [size=" + size + ", type=" + type + "]";
    }

}
