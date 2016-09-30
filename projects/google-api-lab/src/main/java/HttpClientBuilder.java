
import com.google.api.client.googleapis.auth.oauth2.GoogleCredential;
import com.google.api.client.googleapis.services.json.AbstractGoogleJsonClient;
import com.google.api.client.googleapis.util.Utils;

public class HttpClientBuilder extends AbstractGoogleJsonClient.Builder {

    public HttpClientBuilder(String rootUri, String servicePath, GoogleCredential httpRequestInitializer) {
        super(Utils.getDefaultTransport(), Utils.getDefaultJsonFactory(), rootUri, servicePath, httpRequestInitializer,
                false);
    }

    @Override
    public AbstractGoogleJsonClient build() {
        return new DefaultAPICaller(this);
    }

    static class DefaultAPICaller extends AbstractGoogleJsonClient {

        protected DefaultAPICaller(Builder builder) {
            super(builder);
        }

    }

}
