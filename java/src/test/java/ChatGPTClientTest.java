import java.io.FileReader;
import java.io.IOException;
import com.openai.client.OpenAIClient;
import com.openai.client.okhttp.OpenAIOkHttpClient;
import com.openai.core.http.StreamResponse;
import com.openai.models.ChatCompletionChunk;
import com.openai.models.ChatCompletionCreateParams;
import com.openai.models.ChatCompletionMessageParam;
import com.openai.models.ChatCompletionUserMessageParam;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

public class ChatGPTClientTest {
    public static void main(String[] args){
        String apiKey = null;
        
        try {
            // 讀取 config.json 文件的相對路徑
            String configFilePath = "java/src/main/resources/config.json";
            FileReader reader = new FileReader(configFilePath);

            // 使用 Gson 解析 JSON 文件
            JsonObject jsonObject = JsonParser.parseReader(reader).getAsJsonObject();
            apiKey = jsonObject.get("OPENAI_API_KEY").getAsString();

            if (apiKey == null || apiKey.isEmpty()) {
                throw new IllegalStateException("API Key is missing in config.json");
            }
        } catch (IOException e) {
            System.err.println("Failed to read config.json file: " + e.getMessage());
        }

        // 初始化 OpenAI 客戶端
        OpenAIClient client = OpenAIOkHttpClient.builder()
            .apiKey(apiKey)
            .build();

        // 建立 Chat Completion 請求參數
        ChatCompletionCreateParams params = ChatCompletionCreateParams.builder()
            .addMessage(ChatCompletionMessageParam.ofChatCompletionUserMessageParam(
                ChatCompletionUserMessageParam.builder()
                    .role(ChatCompletionUserMessageParam.Role.USER)
                    .content(ChatCompletionUserMessageParam.Content.ofTextContent(
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
                            "Q11. 1.2, 1, 1.3, 0.5"
                    ))
                    .build()
            ))
            .model("o1-mini")
            .build();
        
        long startTime = System.currentTimeMillis(); // 開始時間
        try (StreamResponse<ChatCompletionChunk> messageStreamResponse = client.chat().completions().createStreaming(params)) {
            messageStreamResponse.stream()
                    .flatMap(completion -> completion.choices().stream())
                    .flatMap(choice -> choice.delta().content().stream())
                    .forEach(System.out::print);
        } catch (Exception e) {
            System.out.println(e.getMessage());
        }
        long endTime = System.currentTimeMillis(); // 結束時間
        double responseTimeInSeconds = (endTime - startTime) / 1000.0; // 轉換為秒
        System.out.printf("API Response Time: %.2f seconds%n", responseTimeInSeconds);
    }
}    
