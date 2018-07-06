import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

public class CssLoader {

    public CssLoader() throws IOException {
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        try (InputStream input = CssLoader.class.getResourceAsStream("/base.css")) {
            while (true) {
                int data = input.read();
                if (data == -1) {
                    break;
                }
                output.write(data);
            }
        }
        System.out.println(new String(output.toByteArray(), StandardCharsets.UTF_8));
    }

    public static void main(String[] args) throws IOException {
        new CssLoader();
    }
}
