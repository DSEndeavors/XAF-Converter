import React from "react";
import { Card, Checkbox, Badge, Button, Space, Typography } from "antd";
import { DatabaseOutlined } from "@ant-design/icons";

const { Text } = Typography;

const DataTypeSelector = ({ dataTypes, selected, onChange }) => {
  if (!dataTypes || dataTypes.length === 0) return null;

  const allNames = dataTypes.map((dt) => dt.name);
  const allSelected = selected.length === dataTypes.length;
  const noneSelected = selected.length === 0;

  const handleToggle = (name) => {
    if (selected.includes(name)) {
      onChange(selected.filter((s) => s !== name));
    } else {
      onChange([...selected, name]);
    }
  };

  return (
    <Card
      title={
        <span>
          <DatabaseOutlined style={{ marginRight: 8 }} />
          Data Types
        </span>
      }
      extra={
        <Text type="secondary" style={{ fontSize: 13 }}>
          {selected.length} of {dataTypes.length} selected
        </Text>
      }
    >
      <div className="data-type-actions">
        <Button
          size="small"
          onClick={() => onChange(allNames)}
          disabled={allSelected}
        >
          Select All
        </Button>
        <Button
          size="small"
          onClick={() => onChange([])}
          disabled={noneSelected}
        >
          Deselect All
        </Button>
      </div>
      <div className="data-type-list">
        {dataTypes.map((dt) => {
          const isSelected = selected.includes(dt.name);
          return (
            <div
              key={dt.name}
              className={`data-type-item ${isSelected ? "selected" : ""}`}
              onClick={() => handleToggle(dt.name)}
            >
              <Checkbox checked={isSelected} style={{ pointerEvents: "none" }}>
                <Text>{dt.display_name}</Text>
              </Checkbox>
              <Badge
                count={dt.record_count?.toLocaleString() || 0}
                showZero
                color={isSelected ? "#4A7FB5" : "#999"}
                style={{ fontSize: 12 }}
              />
            </div>
          );
        })}
      </div>
    </Card>
  );
};

export default DataTypeSelector;
