import React from "react";
import { Upload, Typography, Card, Row, Col, message } from "antd";
import {
  InboxOutlined,
  FileExcelOutlined,
  FileTextOutlined,
  CodeOutlined,
  HddOutlined,
} from "@ant-design/icons";

const { Dragger } = Upload;
const { Text, Paragraph } = Typography;

const MAX_SIZE_MB = 250;
const MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024;

const FORMATS = [
  { icon: <FileTextOutlined style={{ fontSize: 20, color: "#4A7FB5" }} />, label: "CSV" },
  { icon: <FileExcelOutlined style={{ fontSize: 20, color: "#4A7FB5" }} />, label: "XLSX" },
  { icon: <CodeOutlined style={{ fontSize: 20, color: "#4A7FB5" }} />, label: "JSON" },
  { icon: <HddOutlined style={{ fontSize: 20, color: "#4A7FB5" }} />, label: "Parquet" },
];

const UploadStep = ({ onUpload, uploading }) => {
  const props = {
    name: "file",
    multiple: false,
    accept: ".xaf,.xml",
    showUploadList: false,
    customRequest: ({ file }) => {
      onUpload(file);
    },
    beforeUpload: (file) => {
      if (file.size > MAX_SIZE_BYTES) {
        message.error(`File is too large. Maximum size is ${MAX_SIZE_MB}MB.`);
        return Upload.LIST_IGNORE;
      }
      const ext = file.name.split(".").pop().toLowerCase();
      if (!["xaf", "xml"].includes(ext)) {
        message.error("Only .xaf and .xml files are supported.");
        return Upload.LIST_IGNORE;
      }
      return true;
    },
    disabled: uploading,
  };

  return (
    <>
      <Dragger {...props} className="upload-dragger">
        <p>
          <InboxOutlined className="upload-icon" />
        </p>
        <Typography.Title level={4}>
          {uploading ? "Uploading..." : "Drop your XAF file here"}
        </Typography.Title>
        <Text type="secondary">
          Click or drag a <strong>.xaf</strong> or <strong>.xml</strong> file to
          this area. Maximum file size: {MAX_SIZE_MB}MB.
        </Text>
      </Dragger>

      <Card style={{ marginTop: 24 }}>
        <Typography.Title level={5} style={{ marginTop: 0 }}>
          What is a XAF file?
        </Typography.Title>
        <Paragraph type="secondary">
          XAF (XML Auditfile Financieel) is the Dutch standard for exchanging
          financial administration data. Accounting software such as Exact Online,
          Twinfield, AFAS, and others can export your general ledger, journal
          entries, customer/supplier data, and more into this format.
        </Paragraph>

        <Typography.Title level={5}>
          What does this tool do?
        </Typography.Title>
        <Paragraph type="secondary">
          XAF Converter parses your XAF file and lets you preview and export the
          data to common formats. Select the data types you need, choose your
          output format, and download instantly.
        </Paragraph>

        <Row gutter={16} style={{ marginTop: 16 }}>
          {FORMATS.map((f) => (
            <Col key={f.label} span={6} style={{ textAlign: "center" }}>
              {f.icon}
              <div><Text type="secondary" style={{ fontSize: 12 }}>{f.label}</Text></div>
            </Col>
          ))}
        </Row>

        <Paragraph type="secondary" style={{ marginTop: 16, marginBottom: 0, fontSize: 12 }}>
          Supports XAF versions 3.1, 3.2, and 4.x. This application runs in a
          Docker instance of your choice — all data stays within your own
          infrastructure and under your full control. Nothing is sent to external
          services.
        </Paragraph>
      </Card>
    </>
  );
};

export default UploadStep;
