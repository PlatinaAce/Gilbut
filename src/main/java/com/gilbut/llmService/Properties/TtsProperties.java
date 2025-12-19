package com.gilbut.llmService.Properties;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Data
@Configuration
@ConfigurationProperties(prefix = "tts.websocket")
public class TtsProperties {
    private String uri;
}
