import React from "react";
import { Progress, Typography } from "antd";
import { LoadingOutlined } from "@ant-design/icons";

const { Text, Title } = Typography;

const ExportProgress = ({ progress, statusMessage }) => {
  const percent = Math.round(progress || 0);

  return (
    <div className="parsing-progress">
      <LoadingOutlined style={{ fontSize: 32, color: "#4A7FB5" }} spin />
      <Title level={4} style={{ margin: 0 }}>
        Exporting...
      </Title>
      <Progress
        percent={percent}
        status="active"
        strokeColor={{
          "0%": "#4A7FB5",
          "100%": "#52c41a",
        }}
        style={{ maxWidth: 500, width: "100%" }}
      />
      {statusMessage && <Text type="secondary">{statusMessage}</Text>}
    </div>
  );
};

export default ExportProgress;
