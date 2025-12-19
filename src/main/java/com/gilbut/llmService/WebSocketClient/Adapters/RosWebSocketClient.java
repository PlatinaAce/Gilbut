package com.gilbut.llmService.WebSocketClient.Adapters;

import com.gilbut.llmService.Properties.RosProperties;
import com.gilbut.llmService.WebSocketClient.BaseWebSocketClient;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.net.URI;

@Slf4j
@Component
public class RosWebSocketClient extends BaseWebSocketClient {
    public RosWebSocketClient(RosProperties rosProperties) {
        super(createUri(rosProperties));
    }

    private static URI createUri(RosProperties rosProperties) {
        try {
            return new URI(rosProperties.getUri());
        } catch (Exception e) {
            throw new IllegalStateException("[RosWebSocketClient] 존재하지 않는 URI: " + rosProperties.getUri(), e);
        }
    }
}
