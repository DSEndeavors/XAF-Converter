/**
 * Create a WebSocket connection for progress updates.
 *
 * @param {string} sessionId
 * @param {(data: {stage: string, progress: number, message: string}) => void} onMessage
 * @param {() => void} [onClose]
 * @returns {{ close: () => void }}
 */
export function connectProgress(sessionId, onMessage, onClose) {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = window.location.host;
  const url = `${protocol}//${host}/ws/progress/${sessionId}`;

  const ws = new WebSocket(url);

  ws.onopen = () => {
    // Connection established
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      // Skip the initial "connected" message
      if (data.stage === "connected") return;
      // Normalize: backend sends "percentage", frontend expects "progress"
      if (data.percentage !== undefined && data.progress === undefined) {
        data.progress = data.percentage;
      }
      onMessage(data);
    } catch {
      // Ignore non-JSON messages
    }
  };

  ws.onerror = () => {
    // Errors are followed by close, handled there
  };

  ws.onclose = () => {
    if (onClose) onClose();
  };

  return {
    close: () => {
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
    },
  };
}
