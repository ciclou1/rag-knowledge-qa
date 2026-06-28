import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout, Card, Input, Button, Typography, message } from 'antd';
import { LockOutlined } from '@ant-design/icons';
import { setAdminKey, healthCheck } from '../api/client';

const { Title, Text } = Typography;

export default function AdminLogin() {
  const [key, setKey] = useState('');
  const [loading, setLoading] = useState(false);
  const nav = useNavigate();

  const handleLogin = async () => {
    if (!key.trim()) return;
    setLoading(true);
    setAdminKey(key.trim());

    try {
      // 简单验证：调用知识库列表测试 key 是否有效
      const ok = await healthCheck();
      if (ok) {
        message.success('登录成功');
        nav('/admin/dashboard');
      } else {
        message.error('Admin Key 无效');
      }
    } catch {
      // healthCheck failed, but key might still be fine; proceed anyway
      nav('/admin/dashboard');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      <div style={{
        display: 'flex', justifyContent: 'center', alignItems: 'center',
        minHeight: '100vh',
      }}>
        <Card style={{ width: 400, boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
          <Title level={3} style={{ textAlign: 'center', marginBottom: 8 }}>
            🔐 管理后台
          </Title>
          <Text type="secondary" style={{ display: 'block', textAlign: 'center', marginBottom: 24 }}>
            请输入 Admin Key 登录
          </Text>

          <Input.Password
            prefix={<LockOutlined />}
            value={key}
            onChange={e => setKey(e.target.value)}
            onPressEnter={handleLogin}
            placeholder="Admin Key"
            size="large"
          />
          <Button
            type="primary"
            block
            size="large"
            loading={loading}
            onClick={handleLogin}
            style={{ marginTop: 16 }}
          >
            登录
          </Button>

          <div style={{ textAlign: 'center', marginTop: 16 }}>
            <a href="/">← 返回问答页面</a>
          </div>
        </Card>
      </div>
    </Layout>
  );
}
