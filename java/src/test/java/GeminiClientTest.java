import com.google.auth.oauth2.GoogleCredentials;
import com.google.cloud.vertexai.VertexAI;
import com.google.cloud.vertexai.api.GenerateContentResponse;
import com.google.cloud.vertexai.generativeai.GenerativeModel;
import com.google.cloud.vertexai.generativeai.ResponseHandler;
import java.io.FileInputStream;
import java.io.IOException;
import java.nio.file.Paths;
import java.nio.file.Path;
import java.io.File;

public class GeminiClientTest {
    public static void main(String[] args) throws IOException{
        String projectId = "gen-lang-client-0612946846"; // Google Cloud 專案 ID
        String location = "us-central1"; // Vertex AI 位置
        String modelName = "gemini-1.5-pro";
        String textPrompt =
            "Stock Trading Rules:"+
            "1. Today's price : The last number in each sequence represents today's price. Today's price is excluded from determining whether a value is a peak or trough."+
            "2. Peak : It is the local maximum in the sequence before today, meaning it is greater than its immediate left and right neighbors at a specific position and appears only once at that position."+
            "3. Trough : It is the local minimum in the sequence before today, meaning it is less than its immediate left and right neighbors at a specific position and appears only once at that position."+
            "4. Buy Condition : Buy when today's price (the last number) is strictly greater than the peak(the unique maximum value in the sequence before today)."+
            "5. Sell Condition : Sell when today's price (the last number) is strictly less than the through(the unique minimum value in the sequence before today)."+
            "6. No Action Condition : Take no action when today's price (the last number) is equal to or between the peak and the trough, or if there is no peak or trough."+
            "Instructions:"+
            "Based on the prices preceding today (i.e., the numbers before the last one), determine the action for each period, and indicate the appropriate action."+
            "Please briefly answer the following questions using step-by-step reasoning to show your work and explanation of the all process for finding a peak and a trough(according to the peak and trough rules). Do not answer any other question."+
            "Question :"+
            "Q1. 1, 1, 2, 1, 3, 3, 2, 5"+
            "Q2. 3, 3, 2, 2, 3, 3, 1"+
            "Q3. 1, 2, 3, 2, 5"+
            "Q4. 1, 1, 1, 5"+
            "Q5. 1, 2, 3, 4, 5"+
            "Q6. 1, 2, 3, 4, 5, 5"+
            "Q7. 2, 3, 4, 1"+
            "Q8. 2, 1, 3, 5, 4, 2"+
            "Q9. 2, 2, 2, 3, 2, 1"+
            "Q10. 1.2, 1.0, 1.3, 0.5"+
            "Q11. 1.2, 1, 1.3, 0.5";

        String output = textInput(projectId, location, modelName, textPrompt); // 呼叫 textInput
        System.out.println(output);
    }

    public static String textInput(
        String projectId, String location, String modelName, String textPrompt) throws IOException {
        
        // 使用相對路徑定位金鑰檔案
        Path keyFilePath = Paths.get("java", "credentials", "gen-lang-client-0612946846-51676805a977.json");
        // 將相對路徑轉為絕對路徑
        String absolutePath = keyFilePath.toAbsolutePath().toString();
        // 建立 GoogleCredentials 並設定範圍
        GoogleCredentials credentials = GoogleCredentials
            .fromStream(new FileInputStream(absolutePath))
         .createScoped("https://www.googleapis.com/auth/cloud-platform");
        
        // 驗證金鑰檔案是否存在
        File keyFile = new File(absolutePath);
        if (keyFile.exists()) {
            System.out.println("檔案存在，路徑正確！");
        } else {
            System.out.println("檔案不存在，請確認路徑：" + keyFile.getAbsolutePath());
        }

        // 計算 API 請求回應時間（開始時間）
        long startTime = System.currentTimeMillis();
        // 初始化 Vertex AI 環境
        try (VertexAI vertexAI = new VertexAI(projectId, location, credentials)) {
            // 初始化 GenerativeModel，指定模型名稱
            GenerativeModel model = new GenerativeModel(modelName, vertexAI);
            // 呼叫 generateContent 方法生成內容
            GenerateContentResponse response = model.generateContent(textPrompt);
            String output = ResponseHandler.getText(response); // 提取回應內容
        // 計算 API 回應時間（結束時間）
        long endTime = System.currentTimeMillis();
        double responseTimeInSeconds = (endTime - startTime) / 1000.0; // 轉換為秒
        System.out.printf("API Response Time: %.2f seconds%n", responseTimeInSeconds);
        
        return output;
    }
  }
}


