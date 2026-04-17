import React from "react";
import { Button, Popconfirm } from "antd";
import { ReloadOutlined } from "@ant-design/icons";

const NewSessionButton = ({ onRestart, loading }) => (
  <Popconfirm
    title="Start new session?"
    description="This will clear the current file and selections."
    onConfirm={onRestart}
    okText="Yes"
    cancelText="Cancel"
    placement="bottomRight"
  >
    <Button icon={<ReloadOutlined />} loading={loading}>
      New Session
    </Button>
  </Popconfirm>
);

export default NewSessionButton;
