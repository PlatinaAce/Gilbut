package com.gilbut.llmService.WebSocketClient.Adapters;

import com.gilbut.llmService.Properties.TtsProperties;
import com.gilbut.llmService.WebSocketClient.BaseWebSocketClient;
import org.springframework.stereotype.Component;

import java.net.URI;

@Component
public class TtsWebSocketClient extends BaseWebSocketClient {
    public TtsWebSocketClient(TtsProperties ttsProperties) {
        super(createUri(ttsProperties));
    }

    private static URI createUri(TtsProperties ttsProperties) {
        try {
            return new URI(ttsProperties.getUri());
        } catch (Exception e) {
            throw new IllegalStateException("[TtsWebSocketClient] 존재하지 않는 URI: " + ttsProperties.getUri(), e);
        }
    }
}
