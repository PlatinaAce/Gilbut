package com.gilbut.simpleTestServer.DTO.TtsMessageDTO;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class TtsMessageDTO {
    private TtsStatusType status;
    private String tts_message;
    private long time;
}
