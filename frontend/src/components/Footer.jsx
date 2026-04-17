import React from "react";
import { Layout, Typography } from "antd";

const { Footer: AntFooter } = Layout;
const { Text } = Typography;

const Footer = () => (
  <AntFooter className="app-footer">
    <Text type="secondary" style={{ fontSize: 13 }}>
      an{" "}
      <a href="https://www.endeavors.nl" target="_blank" rel="noopener noreferrer">
        Endeavors
      </a>{" "}
      initiative
    </Text>
  </AntFooter>
);

export default Footer;
