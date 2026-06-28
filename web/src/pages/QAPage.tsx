import { useState, useEffect } from 'react';
import {
  Layout, Typography, Card, Input, Button, Checkbox,
  Spin, Alert, Space, Tag, Flex, Empty,
} from 'antd';
import {
  SendOutlined, BookOutlined, FileTextOutlined, LinkOutlined, GithubOutlined,
} from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import { qaGet, qaPost } from '../api/client';

const { Header, Content, Footer } = Layout;
const { Title, Text, Paragraph } = Typography;

interface KBItem {
  id: string;
  name: string;
  description: string;
}

interface Source {
  doc_name: string;
  content_snippet: string;
  relevance_score: number;
}

interface QAResult {
  answer: string;
  sources: Source[];
  confidence: string;
}

export default function QAPage() {
  const [kbs, setKbs] = useState<KBItem[]>([]);
  const [selectedKBs, setSelectedKBs] = useState<string[]>([]);
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QAResult | null>(null);
  const [error, setError] = useState('');

  // 加载公开知识库
  useEffect(() => {
    qaGet<KBItem[]>('/knowledge-bases').then(setKbs).catch(console.error);
  }, []);

  const handleAsk = async () => {
    if (!question.trim() || selectedKBs.length === 0) return;
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const data = await qaPost<QAResult>('/ask', {
        question: question.trim(),
        kb_ids: selectedKBs,
        top_k: 5,
      });
      setResult(data);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e.message || '请求失败');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleAsk();
    }
  };

  const confTagColor = {
    high: 'green',
    medium: 'orange',
    low: 'red',
  } as const;

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        background: '#1677ff', padding: '0 24px',
      }}>
        <Title level={3} style={{ color: '#fff', margin: 0 }}>
          📚 RAG 知识问答
        </Title>
        <Space>
          <a href="https://github.com" target="_blank" rel="noreferrer">
            <GithubOutlined style={{ color: '#fff', fontSize: 20 }} />
          </a>
          <a href="/admin/login" style={{ color: '#fff' }}>管理后台</a>
        </Space>
      </Header>

      <Content style={{ padding: '24px 48px', maxWidth: 900, margin: '0 auto', width: '100%' }}>
        {/* 知识库选择 */}
        <Card style={{ marginBottom: 24 }}>
          <Title level={5} style={{ marginBottom: 16 }}>
            <BookOutlined /> 选择知识库（可多选）
          </Title>
          {kbs.length === 0 ? (
            <Text type="secondary">暂无公开知识库</Text>
          ) : (
            <Checkbox.Group
              options={kbs.map(kb => ({ label: kb.name, value: kb.id }))}
              value={selectedKBs}
              onChange={vals => setSelectedKBs(vals as string[])}
            />
          )}
        </Card>

        {/* 输入区 */}
        <Card style={{ marginBottom: 24 }}>
          <Input.TextArea
            value={question}
            onChange={e => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入你的问题，按 Enter 发送..."
            autoSize={{ minRows: 2, maxRows: 4 }}
            style={{ marginBottom: 12 }}
          />
          <Flex justify="space-between" align="center">
            <Text type="secondary">
              {selectedKBs.length === 0
                ? '请先选择知识库'
                : `已选 ${selectedKBs.length} 个知识库`}
            </Text>
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={handleAsk}
              loading={loading}
              disabled={!question.trim() || selectedKBs.length === 0}
            >
              提问
            </Button>
          </Flex>
        </Card>

        {/* 加载中 */}
        {loading && (
          <Card>
            <Flex justify="center" style={{ padding: 40 }}>
              <Spin tip="正在检索知识库..." />
            </Flex>
          </Card>
        )}

        {/* 错误 */}
        {error && <Alert type="error" message={error} style={{ marginBottom: 24 }} closable />}

        {/* 回答结果 */}
        {result && (
          <Card
            title={
              <Space>
                <span>📝 回答</span>
                <Tag color={confTagColor[result.confidence as keyof typeof confTagColor] || 'default'}>
                  {result.confidence === 'high' ? '高置信度' : result.confidence === 'medium' ? '中置信度' : '低置信度'}
                </Tag>
              </Space>
            }
          >
            <div style={{ lineHeight: 1.8, fontSize: 15 }}>
              <ReactMarkdown>{result.answer}</ReactMarkdown>
            </div>

            {result.sources.length > 0 && (
              <>
                <Title level={5} style={{ marginTop: 24 }}>
                  <FileTextOutlined /> 参考来源
                </Title>
                {result.sources.map((s, i) => (
                  <Card key={i} size="small" style={{ marginBottom: 8 }}>
                    <Flex justify="space-between" align="center">
                      <Space>
                        <Tag>{s.doc_name}</Tag>
                      </Space>
                      <Tag color="blue">相关性 {(s.relevance_score * 100).toFixed(0)}%</Tag>
                    </Flex>
                    <Paragraph
                      ellipsis={{ rows: 2 }}
                      style={{ marginTop: 8, color: '#666', fontSize: 13 }}
                    >
                      {s.content_snippet}
                    </Paragraph>
                  </Card>
                ))}
              </>
            )}
          </Card>
        )}

        {/* 空状态 */}
        {!result && !loading && !error && (
          <Empty description="选择一个知识库，开始提问吧" />
        )}
      </Content>

      <Footer style={{ textAlign: 'center', color: '#999' }}>
        RAG Knowledge QA © 2026 · Powered by DeepSeek + Supabase
      </Footer>
    </Layout>
  );
}
