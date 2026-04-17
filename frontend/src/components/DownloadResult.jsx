import React from "react";
import { Button, Result, Space } from "antd";
import { DownloadOutlined, ArrowLeftOutlined } from "@ant-design/icons";

const DownloadResult = ({ downloadUrl, onExportAnother }) => {
  return (
    <div className="download-result">
      <Result
        status="success"
        title="Export complete!"
        subTitle="Your file is ready to download."
        extra={
          <Space direction="vertical" size="middle">
            <Button
              type="primary"
              size="large"
              icon={<DownloadOutlined />}
              href={downloadUrl}
              target="_blank"
            >
              Download File
            </Button>
            <Button
              icon={<ArrowLeftOutlined />}
              onClick={onExportAnother}
            >
              Export another format
            </Button>
          </Space>
        }
      />
    </div>
  );
};

export default DownloadResult;
