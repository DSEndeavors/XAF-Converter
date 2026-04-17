import React from "react";
import { Collapse, Tag, Typography, Space } from "antd";
import {
  SafetyCertificateOutlined,
  CheckCircleFilled,
  CloseCircleFilled,
  DollarOutlined,
} from "@ant-design/icons";

const { Text } = Typography;

const ValidationCard = ({ validation }) => {
  if (!validation || !validation.checks || validation.checks.length === 0) {
    return null;
  }

  const { checks, all_passed, summary } = validation;

  // Group checks by section
  const sections = {};
  for (const c of checks) {
    if (!sections[c.section]) sections[c.section] = [];
    sections[c.section].push(c);
  }

  const header = (
    <Space>
      <SafetyCertificateOutlined />
      <span>Data Integrity</span>
      <Tag
        color={all_passed ? "success" : "error"}
        style={{ fontWeight: 600 }}
      >
        {all_passed ? "VERIFIED" : "MISMATCH"}
      </Tag>
      <Text type="secondary" style={{ fontSize: 12 }}>
        {summary}
      </Text>
    </Space>
  );

  const content = (
    <div className="validation-content">
      {/* Column headers */}
      <div className="validation-grid validation-grid-header">
        <Text type="secondary" style={{ fontSize: 11 }}></Text>
        <Text type="secondary" style={{ fontSize: 11 }}>Check</Text>
        <Text type="secondary" style={{ fontSize: 11, textAlign: "right" }}>XAF</Text>
        <Text type="secondary" style={{ fontSize: 11, textAlign: "right" }}>Computed</Text>
      </div>

      {Object.entries(sections).map(([section, sectionChecks]) => (
        <div key={section} className="validation-section">
          <Text strong style={{ fontSize: 12, display: "block", marginBottom: 4, marginTop: 8 }}>
            {section}
          </Text>
          {sectionChecks.map((c, idx) => {
            const isPL = section === "P&L Summary";
            const isNetResult = isPL && c.check === "Net Result";

            return (
              <div key={idx} className={`validation-grid validation-grid-row ${isNetResult ? "validation-net-result" : ""}`}>
                <span>
                  {isPL ? (
                    <DollarOutlined style={{ color: "#D4891A", fontSize: 14 }} />
                  ) : c.passed ? (
                    <CheckCircleFilled style={{ color: "#52c41a", fontSize: 14 }} />
                  ) : (
                    <CloseCircleFilled style={{ color: "#ff4d4f", fontSize: 14 }} />
                  )}
                </span>
                <Text style={{
                  fontSize: 12,
                  fontWeight: isNetResult ? 600 : "normal",
                }}>
                  {c.check}
                </Text>
                <Text type="secondary" style={{ fontSize: 12, textAlign: "right" }}>
                  {c.declared}
                </Text>
                <Text
                  style={{
                    fontSize: 12,
                    textAlign: "right",
                    color: isPL ? undefined : c.passed ? undefined : "#ff4d4f",
                    fontWeight: isNetResult ? 600 : c.passed ? "normal" : 600,
                  }}
                >
                  {c.computed}
                </Text>
              </div>
            );
          })}
        </div>
      ))}
    </div>
  );

  return (
    <Collapse
      className="validation-collapse"
      defaultActiveKey={all_passed ? [] : ["validation"]}
      items={[
        {
          key: "validation",
          label: header,
          children: content,
        },
      ]}
    />
  );
};

export default ValidationCard;
