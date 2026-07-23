import { InboxOutlined } from "@ant-design/icons";
import { App, Form, Modal, Select, Upload } from "antd";
import type { UploadFile } from "antd";
import { useState } from "react";

import type { UploadDocumentRequest } from "../types";

const { Dragger } = Upload;

export function UploadDocumentModal({ open, loading, onClose, onSubmit }: { open: boolean; loading: boolean; onClose: () => void; onSubmit: (request: UploadDocumentRequest) => Promise<void> }) {
  const { message } = App.useApp();
  const [form] = Form.useForm<UploadDocumentRequest>();
  const [fileList, setFileList] = useState<UploadFile[]>([]);

  function handleClose() {
    form.resetFields();
    setFileList([]);
    onClose();
  }

  async function handleFinish(values: UploadDocumentRequest) {
    const file = fileList[0]?.originFileObj;
    if (!file) {
      message.warning("请先选择要导入的文档");
      return;
    }
    await onSubmit({ ...values, file });
    handleClose();
  }

  return <Modal title="导入知识文档" open={open} onCancel={handleClose} okText="开始解析" cancelText="取消" confirmLoading={loading} onOk={() => form.submit()} destroyOnHidden><Form form={form} layout="vertical" initialValues={{ category: "业务制度" }} onFinish={handleFinish}><Form.Item label="文档文件"><Dragger accept=".pdf,.docx,.xlsx" maxCount={1} beforeUpload={() => false} fileList={fileList} onChange={({ fileList: next }) => setFileList(next)}><p className="ant-upload-drag-icon"><InboxOutlined /></p><p className="ant-upload-text">点击或拖拽文件到这里</p><p className="ant-upload-hint">支持 PDF、DOCX、XLSX，单个文件最大 50 MB</p></Dragger></Form.Item><Form.Item label="文档分类" name="category" rules={[{ required: true, message: "请选择文档分类" }]}><Select options={["业务制度", "采购管理", "风险管理", "项目管理", "档案管理"].map((value) => ({ value, label: value }))} /></Form.Item></Form></Modal>;
}
