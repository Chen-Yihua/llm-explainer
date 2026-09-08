import com.google.auth.oauth2.GoogleCredentials;
import java.io.IOException;

public class GoogleCredentialsConnectTest {
    public static void main(String[] args) {
        try {
            // 嘗試加載 Application Default Credentials
            GoogleCredentials credentials = GoogleCredentials.getApplicationDefault();
            System.out.println("Successfully loaded credentials: " + credentials.toString());
        } catch (IOException e) {
            System.err.println("Failed to load credentials: " + e.getMessage());
        }
    }
}
