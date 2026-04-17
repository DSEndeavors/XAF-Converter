import React, { useState, useCallback, useRef, useEffect } from "react";
import {
  ConfigProvider,
  Layout,
  Typography,
  Steps,
  message,
  Collapse,
  Spin,
  Space,
  Segmented,
  Input,
} from "antd";
import { SunOutlined, MoonOutlined, LaptopOutlined, SearchOutlined } from "@ant-design/icons";

import { darkTheme, lightTheme } from "./styles/theme";
import "./styles/App.css";

import { uploadFile, fetchPreview, exportData, restartSession } from "./api/client";
import { connectProgress } from "./api/websocket";

import UploadStep from "./components/UploadStep";
import ParsingProgress from "./components/ParsingProgress";
import FileInfoCard from "./components/FileInfoCard";
import DataTypeSelector from "./components/DataTypeSelector";
import PreviewTable from "./components/PreviewTable";
import ExportControls from "./components/ExportControls";
import ExportProgress from "./components/ExportProgress";
import DownloadResult from "./components/DownloadResult";
import ValidationCard from "./components/ValidationCard";
import Footer from "./components/Footer";
import NewSessionButton from "./components/NewSessionButton";

const { Header, Content } = Layout;
const { Title } = Typography;

// App phases
const PHASE = {
  UPLOAD: "upload",
  PARSING: "parsing",
  SELECT: "select",
  EXPORTING: "exporting",
  DOWNLOAD: "download",
};

const stepFromPhase = (phase) => {
  switch (phase) {
    case PHASE.UPLOAD:
    case PHASE.PARSING:
      return 0;
    case PHASE.SELECT:
      return 1;
    case PHASE.EXPORTING:
    case PHASE.DOWNLOAD:
      return 2;
    default:
      return 0;
  }
};

const App = () => {
  const [phase, setPhase] = useState(PHASE.UPLOAD);
  const [uploading, setUploading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [fileInfo, setFileInfo] = useState(null);
  const [dataTypes, setDataTypes] = useState([]);
  const [validation, setValidation] = useState(null);
  const [selectedTypes, setSelectedTypes] = useState([]);
  const [previews, setPreviews] = useState({});
  const [previewLoading, setPreviewLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [previewPage, setPreviewPage] = useState(1);
  const [format, setFormat] = useState("csv");
  const [exporting, setExporting] = useState(false);
  const [downloadUrl, setDownloadUrl] = useState(null);
  const [progress, setProgress] = useState(0);
  const [progressMessage, setProgressMessage] = useState("");
  const [progressStage, setProgressStage] = useState("parsing");
  const [restartLoading, setRestartLoading] = useState(false);
  const [themeMode, setThemeMode] = useState("system"); // "light" | "dark" | "system"
  const [systemDark, setSystemDark] = useState(
    window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? true
  );

  const isDark = themeMode === "dark" || (themeMode === "system" && systemDark);

  const wsRef = useRef(null);

  // Listen for system color scheme changes
  useEffect(() => {
    const mq = window.matchMedia?.("(prefers-color-scheme: dark)");
    if (!mq) return;
    const handler = (e) => setSystemDark(e.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  // Clean up WebSocket on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  const resetState = useCallback(() => {
    setPhase(PHASE.UPLOAD);
    setUploading(false);
    setSessionId(null);
    setFileInfo(null);
    setDataTypes([]);
    setValidation(null);
    setSelectedTypes([]);
    setPreviews({});
    setPreviewLoading(false);
    setSearchTerm("");
    setPreviewPage(1);
    setFormat("csv");
    setExporting(false);
    setDownloadUrl(null);
    setProgress(0);
    setProgressMessage("");
    setProgressStage("parsing");
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  // Handle file upload
  const handleUpload = useCallback(async (file) => {
    setUploading(true);
    try {
      const result = await uploadFile(file);
      const sid = result.session_id;
      setSessionId(sid);

      // Start WebSocket for parsing progress
      setPhase(PHASE.PARSING);
      setProgress(0);
      setProgressMessage("Starting...");
      setProgressStage("parsing");

      wsRef.current = connectProgress(
        sid,
        (data) => {
          setProgress(data.progress);
          setProgressMessage(data.message || "");
          setProgressStage(data.stage || "parsing");

          // When parsing reaches 100%, move to select phase
          if (data.stage === "parsing" && data.progress >= 100) {
            setFileInfo(result.file_info);
            setDataTypes(result.data_types || []);
            setValidation(result.validation || null);
            setPhase(PHASE.SELECT);
            if (wsRef.current) {
              wsRef.current.close();
              wsRef.current = null;
            }
          }
        },
        () => {
          // WebSocket closed - if we're still in parsing phase, the upload response
          // already has the data, so just move on
          setPhase((current) => {
            if (current === PHASE.PARSING) {
              setFileInfo(result.file_info);
              setDataTypes(result.data_types || []);
              setValidation(result.validation || null);
              return PHASE.SELECT;
            }
            return current;
          });
        }
      );

      // If parsing is instant (small file / already parsed), the WS might not
      // send progress at all. Use a fallback: if we got file_info directly from
      // upload, transition after a short delay.
      if (result.file_info && result.data_types) {
        setTimeout(() => {
          setPhase((current) => {
            if (current === PHASE.PARSING) {
              setFileInfo(result.file_info);
              setDataTypes(result.data_types || []);
              setValidation(result.validation || null);
              if (wsRef.current) {
                wsRef.current.close();
                wsRef.current = null;
              }
              return PHASE.SELECT;
            }
            return current;
          });
        }, 1000);
      }
    } catch (err) {
      const detail =
        err.response?.data?.detail || err.message || "Upload failed.";
      message.error(detail);
      setPhase(PHASE.UPLOAD);
    } finally {
      setUploading(false);
    }
  }, []);

  // Load preview for selected data types (with search & pagination)
  const loadPreview = useCallback(
    async (types, search, page) => {
      if (types.length === 0) {
        setPreviews({});
        return;
      }
      if (!sessionId) return;

      setPreviewLoading(true);
      try {
        const result = await fetchPreview(sessionId, types, {
          search: search || undefined,
          page,
          pageSize: 50,
        });
        const previewMap = {};
        for (const p of result.previews || []) {
          previewMap[p.data_type] = p;
        }
        setPreviews(previewMap);
      } catch (err) {
        const detail =
          err.response?.data?.detail || err.message || "Preview failed.";
        message.error(detail);
      } finally {
        setPreviewLoading(false);
      }
    },
    [sessionId]
  );

  const handleSelectionChange = useCallback(
    (newSelection) => {
      setSelectedTypes(newSelection);
      setPreviewPage(1);
      loadPreview(newSelection, searchTerm, 1);
    },
    [searchTerm, loadPreview]
  );

  // Debounced search
  const searchTimeout = useRef(null);
  const handleSearch = useCallback(
    (value) => {
      setSearchTerm(value);
      setPreviewPage(1);
      if (searchTimeout.current) clearTimeout(searchTimeout.current);
      searchTimeout.current = setTimeout(() => {
        loadPreview(selectedTypes, value, 1);
      }, 400);
    },
    [selectedTypes, loadPreview]
  );

  const handlePageChange = useCallback(
    (page) => {
      setPreviewPage(page);
      loadPreview(selectedTypes, searchTerm, page);
    },
    [selectedTypes, searchTerm, loadPreview]
  );

  // Handle export
  const handleExport = useCallback(async () => {
    if (!sessionId || selectedTypes.length === 0) {
      message.warning("Please select at least one data type.");
      return;
    }

    setExporting(true);
    setPhase(PHASE.EXPORTING);
    setProgress(0);
    setProgressMessage("Starting export...");
    setProgressStage("exporting");

    // Connect WebSocket for export progress
    wsRef.current = connectProgress(
      sessionId,
      (data) => {
        setProgress(data.progress);
        setProgressMessage(data.message || "");
        setProgressStage(data.stage || "exporting");
      },
      () => {
        // WebSocket closed during export
      }
    );

    try {
      const result = await exportData(sessionId, selectedTypes, format);
      setDownloadUrl(result.download_url);
      setPhase(PHASE.DOWNLOAD);
    } catch (err) {
      const detail =
        err.response?.data?.detail || err.message || "Export failed.";
      message.error(detail);
      setPhase(PHASE.SELECT);
    } finally {
      setExporting(false);
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    }
  }, [sessionId, selectedTypes, format]);

  // Handle restart
  const handleRestart = useCallback(async () => {
    setRestartLoading(true);
    try {
      await restartSession();
    } catch {
      // Ignore errors on restart
    } finally {
      resetState();
      setRestartLoading(false);
    }
  }, [resetState]);

  // Go back to select phase from download
  const handleExportAnother = useCallback(() => {
    setDownloadUrl(null);
    setPhase(PHASE.SELECT);
  }, []);

  // Render current step content
  const renderContent = () => {
    switch (phase) {
      case PHASE.UPLOAD:
        return <UploadStep onUpload={handleUpload} uploading={uploading} />;

      case PHASE.PARSING:
        return (
          <ParsingProgress
            progress={progress}
            statusMessage={progressMessage}
            stage={progressStage}
          />
        );

      case PHASE.SELECT:
        return (
          <div className="select-split">
            <aside className="select-left">
              <FileInfoCard fileInfo={fileInfo} />
              <ValidationCard validation={validation} />
              <div className="export-controls-wrap">
                <ExportControls
                  format={format}
                  onFormatChange={setFormat}
                  onExport={handleExport}
                  exporting={exporting}
                  disabled={selectedTypes.length === 0}
                />
              </div>
              <DataTypeSelector
                dataTypes={dataTypes}
                selected={selectedTypes}
                onChange={handleSelectionChange}
              />
            </aside>
            <section className="select-right">
              {selectedTypes.length === 0 ? (
                <div className="preview-placeholder">
                  Select one or more data types on the left to preview them here.
                </div>
              ) : (
                <>
                  <Input
                    placeholder="Search across all data..."
                    prefix={<SearchOutlined />}
                    allowClear
                    value={searchTerm}
                    onChange={(e) => handleSearch(e.target.value)}
                    style={{ marginBottom: 16 }}
                    size="large"
                  />
                  {previewLoading ? (
                    <div style={{ textAlign: "center", padding: 32 }}>
                      <Spin size="large" tip="Searching..." />
                    </div>
                  ) : Object.keys(previews).length > 0 ? (
                    <Collapse
                      className="preview-collapse"
                      defaultActiveKey={Object.keys(previews)}
                      items={Object.entries(previews).map(
                        ([typeName, data]) => ({
                          key: typeName,
                          label: `${typeName} (${data.total_count} rows)`,
                          children: (
                            <PreviewTable
                              title={typeName}
                              columns={data.columns}
                              rows={data.rows}
                              totalCount={data.total_count}
                              page={previewPage}
                              pageSize={50}
                              onPageChange={handlePageChange}
                            />
                          ),
                        })
                      )}
                    />
                  ) : (
                    <div className="preview-placeholder">
                      No results found.
                    </div>
                  )}
                </>
              )}
            </section>
          </div>
        );

      case PHASE.EXPORTING:
        return (
          <ExportProgress
            progress={progress}
            statusMessage={progressMessage}
          />
        );

      case PHASE.DOWNLOAD:
        return (
          <DownloadResult
            downloadUrl={downloadUrl}
            onExportAnother={handleExportAnother}
          />
        );

      default:
        return null;
    }
  };

  const currentStep = stepFromPhase(phase);

  return (
    <ConfigProvider theme={isDark ? darkTheme : lightTheme}>
      <Layout className={`app-layout ${isDark ? "mode-dark" : "mode-light"}`}>
        <Header className="app-header">
          <Title level={3} className="app-header-title">
            XAF Converter
          </Title>
          <Space size="middle">
            <Segmented
              size="small"
              value={themeMode}
              onChange={setThemeMode}
              options={[
                { value: "light", icon: <SunOutlined /> },
                { value: "system", icon: <LaptopOutlined /> },
                { value: "dark", icon: <MoonOutlined /> },
              ]}
            />
            {sessionId && (
              <NewSessionButton
                onRestart={handleRestart}
                loading={restartLoading}
              />
            )}
          </Space>
        </Header>
        <Content className={`app-content ${phase === PHASE.SELECT ? "app-content--wide" : ""}`}>
          <Steps
            className="app-steps"
            current={currentStep}
            items={[
              { title: "Upload" },
              { title: "Select" },
              { title: "Export" },
            ]}
            size="small"
          />
          {renderContent()}
        </Content>
        <Footer />
      </Layout>
    </ConfigProvider>
  );
};

export default App;
