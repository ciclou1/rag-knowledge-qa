import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Layout, Typography, Card, Button, Modal, Input, Row, Col,
  Switch, Space, Popconfirm, message, Tag, Empty, Spin, Flex,
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, LogoutOutlined,
  BookOutlined, HomeOutlined,
} from '@ant-design/icons';
import { adminGet, adminPost, adminPut, adminDelete, clearAdminKey, isAdminAuthenticated } from '../api/client';

const { Header, Content } = Layout;
const { Title, Text } = Typography;

interface KB {
  id: string;
  name: string;
  description: string;
  is_public: boolean;
  document_count: number;
  created_at: string;
}

export default function AdminDashboard() {
  const [kbs, setKbs] = useState<KB[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingKB, setEditingKB] = useState<KB | null>(null);
  const [formName, setFormName] = useState('');
  const [formDesc, setFormDesc] = useState('');
  const [formPublic, setFormPublic] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const nav = useNavigate();

  useEffect(() => {
    if (!isAdminAuthenticated()) {
      nav('/admin/login');
      return;
    }
    loadKBs();
  }, []);

  const loadKBs = async () => {
    setLoading(true);
    try {
      const data = await adminGet<KB[]>('/knowledge-bases');
      setKbs(data);
    } catch (e: any) {
      if (e?.response?.status === 401) nav('/admin/login');
      else message.error('加载失败');
    } finally {
      setLoading(false);
    }
  };

  const openCreate = () => {
    setEditingKB(null);
    setFormName('');
    setFormDesc('');
    setFormPublic(true);
    setModalOpen(true);
  };

  const openEdit = (kb: KB) => {
    setEditingKB(kb);
    setFormName(kb.name);
    setFormDesc(kb.description);
    setFormPublic(kb.is_public);
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    if (!formName.trim()) return;
    setSubmitting(true);
    try {
      if (editingKB) {
        await adminPut(`/knowledge-bases/${editingKB.id}`, {
          name: formName,
          description: formDesc,
          is_public: formPublic,
        });
        message.success('已更新');
      } else {
        await adminPost('/knowledge-bases', {
          name: formName,
          description: formDesc,
          is_public: formPublic,
        });
        message.success('已创建');
      }
      setModalOpen(false);
      loadKBs();
    } catch {
      message.error('操作失败');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await adminDelete(`/knowledge-bases/${id}`);
      message.success('已删除');
      loadKBs();
    } catch {
      message.error('删除失败');
    }
  };

  const handleLogout = () => {
    clearAdminKey();
    nav('/admin/login');
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        background: '#1677ff', padding: '0 24px',
      }}>
        <Title level={4} style={{ color: '#fff', margin: 0 }}>
          📋 知识库管理
        </Title>
        <Space>
          <a href="/" style={{ color: '#fff' }}><HomeOutlined /> 问答页</a>
          <Button size="small" danger onClick={handleLogout}>
            <LogoutOutlined /> 退出
          </Button>
        </Space>
      </Header>

      <Content style={{ padding: '24px 48px' }}>
        <Flex justify="space-between" align="center" style={{ marginBottom: 24 }}>
          <Title level={4} style={{ margin: 0 }}>
            <BookOutlined /> 知识库列表
          </Title>
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
            新建知识库
          </Button>
        </Flex>

        {loading ? (
          <Spin tip="加载中..." style={{ display: 'block', textAlign: 'center', padding: 60 }} />
        ) : kbs.length === 0 ? (
          <Empty description="暂无知识库，点击上方按钮创建" />
        ) : (
          <Row gutter={[16, 16]}>
            {kbs.map(kb => (
              <Col xs={24} sm={12} lg={8} key={kb.id}>
                <Card
                  hoverable
                  onClick={() => nav(`/admin/kb/${kb.id}`)}
                  actions={[
                    <EditOutlined key="edit" onClick={(e) => { e.stopPropagation(); openEdit(kb); }} />,
                    <Popconfirm
                      key="delete"
                      title="确定删除此知识库及其所有文档？"
                      onConfirm={(e) => { e?.stopPropagation(); handleDelete(kb.id); }}
                    >
                      <DeleteOutlined onClick={(e) => e.stopPropagation()} />
                    </Popconfirm>,
                  ]}
                >
                  <Card.Meta
                    title={
                      <Space>
                        <span>{kb.name}</span>
                        <Tag color={kb.is_public ? 'green' : 'default'}>
                          {kb.is_public ? '公开' : '私有'}
                        </Tag>
                      </Space>
                    }
                    description={
                      <>
                        <Text type="secondary">
                          {kb.description || '无描述'} · {kb.document_count} 篇文档
                        </Text>
                      </>
                    }
                  />
                </Card>
              </Col>
            ))}
          </Row>
        )}

        {/* 创建/编辑弹窗 */}
        <Modal
          title={editingKB ? '编辑知识库' : '新建知识库'}
          open={modalOpen}
          onCancel={() => setModalOpen(false)}
          onOk={handleSubmit}
          confirmLoading={submitting}
          destroyOnClose
        >
          <div style={{ marginBottom: 16 }}>
            <Text>名称</Text>
            <Input
              value={formName}
              onChange={e => setFormName(e.target.value)}
              placeholder="知识库名称"
              style={{ marginTop: 4 }}
            />
          </div>
          <div style={{ marginBottom: 16 }}>
            <Text>描述</Text>
            <Input.TextArea
              value={formDesc}
              onChange={e => setFormDesc(e.target.value)}
              placeholder="可选描述"
              rows={3}
              style={{ marginTop: 4 }}
            />
          </div>
          <div>
            <Space>
              <Text>公开</Text>
              <Switch checked={formPublic} onChange={setFormPublic} />
            </Space>
          </div>
        </Modal>
      </Content>
    </Layout>
  );
}
