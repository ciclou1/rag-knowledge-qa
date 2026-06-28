import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Layout, Typography, Table, Button, Upload, Modal, Input, Space,
  message, Popconfirm, Tag, Flex, Card,
} from 'antd';
import {
  ArrowLeftOutlined, UploadOutlined, DeleteOutlined, PlusOutlined,
} from '@ant-design/icons';
import type { UploadProps } from 'antd';
import { adminGet, adminUpload, adminDelete, adminPut, isAdminAuthenticated } from '../api/client';

const { Header, Content } = Layout;
const { Title, Text } = Typography;

interface KB {
  id: string;
  name: string;
  description: string;
  is_public: boolean;
  document_count: number;
}

interface Doc {
  doc_name: string;
  chunks: number;
  folder: string;
  tags: string[];
  created_at: string;
  knowledge_base_id: string;
}

export default function AdminKBDetail() {
  const { id } = useParams<{ id: string }>();
  const nav = useNavigate();
  const [kb, setKb] = useState<KB | null>(null);
  const [docs, setDocs] = useState<Doc[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [uploadFolder, setUploadFolder] = useState('');
  const [uploadTags, setUploadTags] = useState('');
  const [uploading, setUploading] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editName, setEditName] = useState('');
  const [editDesc, setEditDesc] = useState('');

  useEffect(() => {
    if (!isAdminAuthenticated()) {
      nav('/admin/login');
      return;
    }
    if (id) loadData();
  }, [id]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [kbData, docsData] = await Promise.all([
        adminGet<KB>(`/knowledge-bases/${id}`),
        adminGet<{ items: Doc[] }>(`/knowledge-bases/${id}/documents`),
      ]);
      setKb(kbData);
      setDocs(docsData.items || []);
    } catch (e: any) {
      if (e?.response?.status === 401) nav('/admin/login');
      else message.error('加载失败');
    } finally {
      setLoading(false);
    }
  };

  const handleUpload: UploadProps['customRequest'] = async (options) => {
    const { file, onSuccess, onError } = options as any;
    setUploading(true);
    try {
      const result = await adminUpload(
        `/knowledge-bases/${id}/documents`,
        file,
        uploadFolder,
        uploadTags,
      );
      message.success(`已上传，${result.chunks} 个分块`);
      setUploadModalOpen(false);
      loadData();
      onSuccess?.(result, file);
    } catch (e: any) {
      message.error('上传失败: ' + (e?.response?.data?.detail || e.message));
      onError?.(e);
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteDoc = async (docName: string) => {
    try {
      await adminDelete(`/documents/${encodeURIComponent(docName)}?kb_id=${id}`);
      message.success('已删除');
      loadData();
    } catch {
      message.error('删除失败');
    }
  };

  const handleEditKB = async () => {
    try {
      await adminPut(`/knowledge-bases/${id}`, { name: editName, description: editDesc });
      message.success('已更新');
      setEditModalOpen(false);
      loadData();
    } catch {
      message.error('更新失败');
    }
  };

  const openEditKB = () => {
    if (!kb) return;
    setEditName(kb.name);
    setEditDesc(kb.description);
    setEditModalOpen(true);
  };

  const columns = [
    {
      title: '文档名',
      dataIndex: 'doc_name',
      key: 'doc_name',
      ellipsis: true,
    },
    {
      title: '分块数',
      dataIndex: 'chunks',
      key: 'chunks',
      width: 100,
    },
    {
      title: '文件夹',
      dataIndex: 'folder',
      key: 'folder',
      width: 120,
      render: (v: string) => v || <Text type="secondary">—</Text>,
    },
    {
      title: '标签',
      dataIndex: 'tags',
      key: 'tags',
      width: 200,
      render: (tags: string[]) =>
        tags?.length > 0
          ? tags.map(t => <Tag key={t}>{t}</Tag>)
          : <Text type="secondary">—</Text>,
    },
    {
      title: '上传时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (v: string) => v ? new Date(v).toLocaleString('zh-CN') : '—',
    },
    {
      title: '操作',
      key: 'actions',
      width: 80,
      render: (_: any, record: Doc) => (
        <Popconfirm
          title="确定删除此文档？"
          onConfirm={() => handleDeleteDoc(record.doc_name)}
        >
          <Button type="text" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        background: '#1677ff', padding: '0 24px',
      }}>
        <Space>
          <Button
            type="text"
            icon={<ArrowLeftOutlined />}
            onClick={() => nav('/admin/dashboard')}
            style={{ color: '#fff' }}
          />
          <Title level={4} style={{ color: '#fff', margin: 0 }}>
            {kb?.name || '加载中...'}
          </Title>
          <Tag color={kb?.is_public ? 'green' : 'default'}>
            {kb?.is_public ? '公开' : '私有'}
          </Tag>
        </Space>
        <Space>
          <Button onClick={openEditKB} style={{ color: '#fff' }} type="text">
            编辑信息
          </Button>
        </Space>
      </Header>

      <Content style={{ padding: '24px 48px', maxWidth: 1200, margin: '0 auto', width: '100%' }}>
        {/* 操作栏 */}
        <Flex justify="space-between" align="center" style={{ marginBottom: 16 }}>
          <Text type="secondary">
            {kb?.description} · 共 {docs.length} 篇文档
          </Text>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setUploadModalOpen(true)}
          >
            上传文档
          </Button>
        </Flex>

        {/* 文档列表 */}
        <Table
          columns={columns}
          dataSource={docs}
          rowKey="doc_name"
          loading={loading}
          pagination={{ pageSize: 20, showTotal: (total) => `共 ${total} 篇文档` }}
          locale={{ emptyText: '暂无文档，点击"上传文档"开始' }}
        />

        {/* 上传弹窗 */}
        <Modal
          title="上传文档"
          open={uploadModalOpen}
          onCancel={() => setUploadModalOpen(false)}
          footer={null}
          destroyOnClose
        >
          <div style={{ marginBottom: 16 }}>
            <Text>文件夹（可选）</Text>
            <Input
              value={uploadFolder}
              onChange={e => setUploadFolder(e.target.value)}
              placeholder="如：技术笔记"
              style={{ marginTop: 4 }}
            />
          </div>
          <div style={{ marginBottom: 16 }}>
            <Text>标签（可选，逗号分隔）</Text>
            <Input
              value={uploadTags}
              onChange={e => setUploadTags(e.target.value)}
              placeholder="如：Python, AI"
              style={{ marginTop: 4 }}
            />
          </div>
          <Upload
            customRequest={handleUpload}
            showUploadList={false}
            accept=".pdf,.docx,.doc,.md,.txt,.markdown"
          >
            <Button
              type="primary"
              icon={<UploadOutlined />}
              loading={uploading}
              block
            >
              {uploading ? '上传并处理中...' : '选择文件（PDF/Word/MD/TXT，最大 20MB）'}
            </Button>
          </Upload>
        </Modal>

        {/* 编辑知识库弹窗 */}
        <Modal
          title="编辑知识库信息"
          open={editModalOpen}
          onCancel={() => setEditModalOpen(false)}
          onOk={handleEditKB}
          destroyOnClose
        >
          <div style={{ marginBottom: 16 }}>
            <Text>名称</Text>
            <Input
              value={editName}
              onChange={e => setEditName(e.target.value)}
              style={{ marginTop: 4 }}
            />
          </div>
          <div style={{ marginBottom: 16 }}>
            <Text>描述</Text>
            <Input.TextArea
              value={editDesc}
              onChange={e => setEditDesc(e.target.value)}
              rows={3}
              style={{ marginTop: 4 }}
            />
          </div>
        </Modal>
      </Content>
    </Layout>
  );
}
