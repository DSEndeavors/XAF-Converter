import React from "react";
import { Card, Typography } from "antd";
import { FileTextOutlined } from "@ant-design/icons";

const { Text } = Typography;

const InfoRow = ({ label, value }) => (
  <>
    <Text type="secondary" className="info-label">{label}</Text>
    <Text className="info-value">{value || "-"}</Text>
  </>
);

const FileInfoCard = ({ fileInfo }) => {
  if (!fileInfo) return null;

  return (
    <Card className="file-info-card" title={
      <span>
        <FileTextOutlined style={{ marginRight: 8 }} />
        File Information
      </span>
    }>
      {/* Company spans full width */}
      <div className="info-grid info-grid-full">
        <InfoRow label="Company" value={fileInfo.company_name} />
      </div>

      {/* Two-column layout for the rest */}
      <div className="info-grid info-grid-split">
        <InfoRow label="XAF Version" value={fileInfo.xaf_version} />
        <InfoRow label="Fiscal Year" value={fileInfo.fiscal_year} />
        <InfoRow label="Currency" value={fileInfo.currency} />
        <InfoRow label="Start Date" value={fileInfo.start_date} />
        <InfoRow label="Software" value={fileInfo.software} />
        <InfoRow label="End Date" value={fileInfo.end_date} />
      </div>
    </Card>
  );
};

export default FileInfoCard;
