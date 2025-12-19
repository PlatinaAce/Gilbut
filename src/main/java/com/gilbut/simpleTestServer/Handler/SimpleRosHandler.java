package com.gilbut.simpleTestServer.Handler;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.gilbut.simpleTestServer.DTO.RosMessageDTO.RosMessageDTO;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.TextWebSocketHandler;

@Slf4j
@Component
@RequiredArgsConstructor
public class SimpleRosHandler extends TextWebSocketHandler {

    private final ObjectMapper objectMapper;

    @Override
    public void afterConnectionEstablished(WebSocketSession session) {
        log.info("[ROS SERVER] 클리이언트 연결: {}", session.getId());
    }

    @Override
    protected void handleTextMessage(WebSocketSession session, TextMessage message) throws Exception {
        RosMessageDTO rosDTO = objectMapper.readValue(message.getPayload(), RosMessageDTO.class);
        log.info("[ROS SERVER] rosDTO.getStatus(): {}", rosDTO.toString());
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) throws Exception {
        log.info("[ROS SERVER] 연결 종료: {}", status.getReason());
    }

    @Override
    public void handleTransportError(WebSocketSession session, Throwable exception) throws Exception {
        log.error("[ROS SERVER] 에러 발생: {}", exception.getMessage());
    }
}
