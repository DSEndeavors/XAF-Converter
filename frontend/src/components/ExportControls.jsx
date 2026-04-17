import React from "react";
import { Card, Segmented, Button, Space } from "antd";
import {
  ExportOutlined,
  FileExcelOutlined,
  FileTextOutlined,
  CodeOutlined,
  HddOutlined,
  SendOutlined,
} from "@ant-design/icons";

const FORMAT_OPTIONS = [
  { label: "CSV", value: "csv", icon: <FileTextOutlined /> },
  { label: "XLSX", value: "xlsx", icon: <FileExcelOutlined /> },
  { label: "JSON", value: "json", icon: <CodeOutlined /> },
  { label: "Parquet", value: "parquet", icon: <HddOutlined /> },
];

const ExportControls = ({
  format,
  onFormatChange,
  onExport,
  exporting,
  disabled,
}) => {
  return (
    <Card
      title={
        <span>
          <SendOutlined style={{ marginRight: 8 }} />
          Export Format
        </span>
      }
    >
      <Segmented
        className="format-selector"
        options={FORMAT_OPTIONS.map((opt) => ({
          label: (
            <Space size={4}>
              {opt.icon}
              {opt.label}
            </Space>
          ),
          value: opt.value,
        }))}
        value={format}
        onChange={onFormatChange}
        size="middle"
        block
      />
      <div style={{ marginTop: 12, textAlign: "center" }}>
        <Button
          type="primary"
          icon={<ExportOutlined />}
          onClick={onExport}
          loading={exporting}
          disabled={disabled || exporting}
          style={{ minWidth: 140 }}
        >
          {exporting ? "Exporting..." : "Export"}
        </Button>
      </div>
    </Card>
  );
};

export default ExportControls;
