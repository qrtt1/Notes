package org.qrtt1.media;

public class Box {

    long start;
    long end;
    long size;
    String type;
    Box parent;
    boolean needParent;

    @Override
    public String toString() {
        StringBuilder builder = new StringBuilder(
                "Box [type=" + type + ", size=" + size + ", start=" + start + ", end=" + end + "]");
        for (int i = 0; i < deep(); i++) {
            builder.insert(0, "\t");
        }
        return builder.toString();
    }

    private int deep() {
        Box root = this;
        int count = 0;
        while (root.parent != null) {
            root = root.parent;
            count++;
        }
        return count;
    }

    public boolean hasChildren() {
        if ("moov".equals(type)) {
            return true;
        }
        if ("trak".equals(type)) {
            return true;
        }
        if ("mdia".equals(type)) {
            return true;
        }

        return false;
    }

}
