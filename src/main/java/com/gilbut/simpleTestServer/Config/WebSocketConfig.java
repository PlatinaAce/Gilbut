package com.gilbut.simpleTestServer.Config;

import com.gilbut.simpleTestServer.Handler.SimpleRosHandler;
import com.gilbut.simpleTestServer.Handler.SimpleTtsHandler;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.socket.WebSocketHandler;
import org.springframework.web.socket.config.annotation.EnableWebSocket;
import org.springframework.web.socket.config.annotation.WebSocketConfigurer;
import org.springframework.web.socket.config.annotation.WebSocketHandlerRegistry;

@Configuration
@EnableWebSocket
@RequiredArgsConstructor
public class WebSocketConfig implements WebSocketConfigurer {
    private final SimpleRosHandler simpleRosHandler;
    private final SimpleTtsHandler simpleTtsHandler;

    @Override
    public void registerWebSocketHandlers(WebSocketHandlerRegistry registry) {
        register(registry, simpleRosHandler, "/ros");
        register(registry, simpleTtsHandler, "/tts");
    }

    private void register(
            WebSocketHandlerRegistry registry,
            WebSocketHandler webSocketHandler,
            String path
    ) {
        registry.addHandler(webSocketHandler, path)
                .setAllowedOrigins("*");
    }
}
