import { theme } from "antd";

// Brand color — used for identity elements (steps, links, header accents)
const BRAND = "#D4891A";
const BRAND_HOVER = "#E89E2D";

// Action color — muted blue for interactive controls (buttons, segmented, checkboxes)
const ACTION = "#4A7FB5";
const ACTION_HOVER = "#5A92C8";
const ACTION_ACTIVE = "#3A6A9A";

const shared = {
  colorPrimary: ACTION,
  colorLink: BRAND,
  colorLinkHover: BRAND_HOVER,
  borderRadius: 8,
  fontFamily:
    "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
};

const sharedComponents = {
  Steps: {
    colorPrimary: BRAND,
  },
  Button: {
    colorPrimary: ACTION,
    colorPrimaryHover: ACTION_HOVER,
    colorPrimaryActive: ACTION_ACTIVE,
  },
  Checkbox: {
    colorPrimary: ACTION,
    colorPrimaryHover: ACTION_HOVER,
  },
  Progress: {
    colorInfo: ACTION,
  },
  Segmented: {
    itemSelectedBg: ACTION,
    itemSelectedColor: "#fff",
  },
};

export const darkTheme = {
  algorithm: theme.darkAlgorithm,
  token: {
    ...shared,
    colorText: "rgba(255, 255, 255, 0.95)",
    colorTextSecondary: "rgba(255, 255, 255, 0.80)",
    colorTextTertiary: "rgba(255, 255, 255, 0.65)",
    colorTextDescription: "rgba(255, 255, 255, 0.70)",
    colorBgBase: "#141414",
    colorBgContainer: "#1f1f1f",
    colorBgElevated: "#262626",
    colorBorderSecondary: "#303030",
  },
  components: {
    ...sharedComponents,
    Layout: {
      headerBg: "#1a1a1a",
      bodyBg: "#141414",
    },
    Card: {
      colorBgContainer: "#1f1f1f",
    },
    Table: {
      colorBgContainer: "#1f1f1f",
      headerBg: "#262626",
    },
  },
};

export const lightTheme = {
  algorithm: theme.defaultAlgorithm,
  token: {
    ...shared,
    colorText: "rgba(0, 0, 0, 0.90)",
    colorTextSecondary: "rgba(0, 0, 0, 0.70)",
    colorTextTertiary: "rgba(0, 0, 0, 0.55)",
    colorTextDescription: "rgba(0, 0, 0, 0.60)",
    colorBgBase: "#ffffff",
    colorBgContainer: "#ffffff",
    colorBgElevated: "#fafafa",
    colorBorderSecondary: "#e0e0e0",
  },
  components: {
    ...sharedComponents,
    Layout: {
      headerBg: "#ffffff",
      bodyBg: "#f5f5f5",
    },
    Card: {
      colorBgContainer: "#ffffff",
    },
    Table: {
      colorBgContainer: "#ffffff",
      headerBg: "#fafafa",
    },
  },
};

// Default export for backwards compat
export default darkTheme;
