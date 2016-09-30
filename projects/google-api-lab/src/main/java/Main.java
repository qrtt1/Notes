
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStream;
import java.util.HashSet;

import com.google.api.client.googleapis.auth.oauth2.GoogleCredential;
import com.google.api.client.googleapis.services.json.AbstractGoogleJsonClient;
import com.google.api.client.http.GenericUrl;
import com.google.api.client.http.HttpResponse;
import com.google.api.client.util.IOUtils;
import com.google.common.collect.Sets;

public class Main {

    private static final String SERVICE_PATH = "/analytics/v3/data/realtime";
    private static final String ROOT_URI = "https://www.googleapis.com";

    public static void main(String[] args) throws FileNotFoundException, IOException {

        GoogleCredential googleCredential = buildGoogleCredential();
        HttpClientBuilder builder = new HttpClientBuilder(ROOT_URI, SERVICE_PATH, googleCredential);
        AbstractGoogleJsonClient client = builder.build();
        HttpResponse response = client.getRequestFactory().buildGetRequest(buildRequestURL()).execute();
        IOUtils.copy(response.getContent(), System.out);

    }

    protected static GoogleCredential buildGoogleCredential() throws IOException, FileNotFoundException {
        File file = new File(System.getProperty("AUTH_FILE"));
        try (InputStream stream = new FileInputStream(file)) {
            GoogleCredential googleCredential = GoogleCredential.fromStream(stream);
            googleCredential = googleCredential.createScoped(AUTHED_SCOPES());
            return googleCredential;
        }
    }

    protected static GenericUrl buildRequestURL() {
        long gaViewNumber = Long.valueOf(System.getProperty("GA_VIEW_NUMBER"));
        String request = "https://www.googleapis.com/analytics/v3/data/realtime?ids=ga%3A" + gaViewNumber
                + "&metrics=rt%3AactiveUsers";
        return new GenericUrl(request);
    }

    protected static HashSet<String> AUTHED_SCOPES() {
        return Sets.newHashSet("https://www.googleapis.com/auth/analytics.readonly");
    }

}
