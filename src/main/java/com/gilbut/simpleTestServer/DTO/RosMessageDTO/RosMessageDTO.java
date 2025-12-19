package com.gilbut.simpleTestServer.DTO.RosMessageDTO;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class RosMessageDTO {
    // ROS 응답의 타입을 지정한다.
    private RosStatusType status;

    // status 가 ERROR 일 경우, 이하의 값은 초기화하지 않는다.
    private Double pos_x;
    private Double pos_y;
    private Double pos_z;

    private Double ori_x;
    private Double ori_y;
    private Double ori_z;
    private Double ori_w;
}