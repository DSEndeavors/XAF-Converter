import React from "react";
import { Progress, Typography, Space } from "antd";
import { LoadingOutlined } from "@ant-design/icons";

const { Text, Title } = Typography;

const ParsingProgress = ({ progress, statusMessage, stage }) => {
  const percent = Math.round(progress || 0);
  const displayStage = stage === "exporting" ? "Exporting" : "Parsing";

  return (
    <div className="parsing-progress">
      <LoadingOutlined style={{ fontSize: 32, color: "#4A7FB5" }} spin />
      <Title level={4} style={{ margin: 0 }}>
        {displayStage} your XAF file...
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
      {statusMessage && statusMessage !== "Starting..." && (
        <Text type="secondary">{statusMessage}</Text>
      )}
    </div>
  );
};

export default ParsingProgress;
