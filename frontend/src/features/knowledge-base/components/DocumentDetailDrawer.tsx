import { Alert, Button, Descriptions, Drawer, Skeleton, Space, Steps, Tag, Typography } from "antd";
import { RefreshCw } from "lucide-react";

import type { KnowledgeDocument } from "../types";

export function DocumentDetailDrawer({
  document,
  loading,
  onClose,
  onRetry,
}: {
  document: KnowledgeDocument | null;
  loading?: boolean;
  onClose: () => void;
  onRetry: (documentId: number) => void;
}) {
  const steps = [
    { title: "文件准入校验", status: "finish" as const },
    {
      title: "文本解析与清洗",
      status: document?.status === "failed"
        ? "error" as const
        : document?.status === "processing"
          ? "process" as const
          : "finish" as const,
    },
    { title: "章节拆分与切块", status: document?.status === "ready" ? "finish" as const : "wait" as const },
    { title: "向量化与索引", status: document?.status === "ready" ? "finish" as const : "wait" as const },
  ];

  const statusLabel = document?.status === "ready"
    ? "已就绪"
    : document?.status === "failed"
      ? "处理失败"
      : `处理中 ${document?.progress ?? 0}%`;

  const statusColor = document?.status === "ready"
    ? "success"
    : document?.status === "failed"
      ? "error"
      : "processing";

  return (
    <Drawer
      size="large"
      title="文档详情"
      open={Boolean(document)}
      onClose={onClose}
      extra={document ? <Tag color={statusColor}>{statusLabel}</Tag> : undefined}
    >
      {loading ? <Skeleton active paragraph={{ rows: 6 }} /> : <Space direction="vertical" size={22} style={{ width: "100%" }}>
        {document && (
          <>
            <div>
              <Typography.Title level={4}>{document.name}</Typography.Title>
              <Typography.Text type="secondary">最后更新 {document.updatedAt}</Typography.Text>
            </div>

            <Descriptions
              column={2}
              size="small"
              bordered
              items={[
                { key: "type", label: "文件类型", children: document.type },
                { key: "size", label: "文件大小", children: document.size },
                { key: "category", label: "文档分类", children: document.category },
                { key: "version", label: "当前版本", children: document.version },
                { key: "chunks", label: "向量切片", children: document.chunks ? `${document.chunks.toLocaleString()} chunks` : "待处理" },
                { key: "updatedBy", label: "更新人员", children: document.updatedBy },
              ]}
            />

            {document.error && (
              <Alert
                type="error"
                showIcon
                message="处理失败"
                description={document.error}
                action={
                  <Button size="small" icon={<RefreshCw size={13} />} onClick={() => onRetry(document.id)}>
                    重新处理
                  </Button>
                }
              />
            )}

            <div>
              <Typography.Title level={5}>处理流水线</Typography.Title>
              <Steps direction="vertical" size="small" items={steps} />
            </div>
          </>
        )}
      </Space>}
    </Drawer>
  );
}
