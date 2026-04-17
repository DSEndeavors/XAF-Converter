import React from "react";
import { Table, Typography } from "antd";

const PreviewTable = ({ title, columns, rows, totalCount, page, pageSize, onPageChange }) => {
  if (!columns || !rows) return null;

  const tableColumns = columns.map((col) => ({
    title: col,
    dataIndex: col,
    key: col,
    ellipsis: true,
    width: 160,
  }));

  const tableData = rows.map((row, rowIdx) => ({
    key: rowIdx,
    ...row,
  }));

  const hasPagination = totalCount != null && totalCount > (pageSize || 50);

  return (
    <div style={{ marginBottom: 16 }}>
      <Table
        columns={tableColumns}
        dataSource={tableData}
        size="small"
        pagination={
          hasPagination
            ? {
                current: page || 1,
                pageSize: pageSize || 50,
                total: totalCount,
                onChange: onPageChange,
                showSizeChanger: false,
                showTotal: (total) => `${total} rows`,
                size: "small",
              }
            : false
        }
        scroll={{ x: "max-content" }}
        bordered
      />
    </div>
  );
};

export default PreviewTable;
