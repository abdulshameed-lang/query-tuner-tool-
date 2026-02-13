import React, { useEffect, useState } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Spin,
  Alert,
  Typography,
  Tag,
  Descriptions,
  Divider,
  Timeline,
  Row,
  Col,
  Empty,
} from 'antd';
import {
  ReloadOutlined,
  WarningOutlined,
  ClockCircleOutlined,
  DatabaseOutlined,
  UserOutlined,
  ThunderboltOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { oracleService } from '../services/oracleService';

const { Title, Text, Paragraph } = Typography;

interface Session {
  sid: number;
  serial: number;
  username: string;
  sql_id: string;
  program: string;
  machine: string;
  blocking_resource: string;
}

interface Deadlock {
  deadlock_id: number;
  detected_time: string;
  session1: Session;
  session2: Session;
  resource_type: string;
  deadlock_type: string;
  resolution: string;
  duration_seconds: number;
  impact: string;
}

export const DeadlocksPage: React.FC = () => {
  const [deadlocks, setDeadlocks] = useState<Deadlock[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedDeadlock, setSelectedDeadlock] = useState<Deadlock | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchDeadlocks();
  }, []);

  const fetchDeadlocks = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await oracleService.getDeadlocks();
      setDeadlocks(data || []);
      if (data && data.length > 0) {
        setSelectedDeadlock(data[0]);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch deadlocks');
    } finally {
      setLoading(false);
    }
  };

  const getImpactColor = (impact: string) => {
    switch (impact.toUpperCase()) {
      case 'HIGH':
        return 'red';
      case 'MEDIUM':
        return 'orange';
      case 'LOW':
        return 'yellow';
      default:
        return 'default';
    }
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'deadlock_id',
      key: 'deadlock_id',
      width: 60,
      render: (id: number) => <Text strong>#{id}</Text>,
    },
    {
      title: 'Detected Time',
      dataIndex: 'detected_time',
      key: 'detected_time',
      width: 180,
      render: (time: string) => (
        <Space>
          <ClockCircleOutlined />
          {new Date(time).toLocaleString()}
        </Space>
      ),
    },
    {
      title: 'Type',
      dataIndex: 'deadlock_type',
      key: 'deadlock_type',
      width: 100,
      render: (type: string) => <Tag color="purple">{type}</Tag>,
    },
    {
      title: 'Sessions',
      key: 'sessions',
      width: 150,
      render: (_: any, record: Deadlock) => (
        <Space direction="vertical" size={0}>
          <Text>
            <UserOutlined /> SID {record.session1.sid} ↔ SID {record.session2.sid}
          </Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {record.session1.username}
          </Text>
        </Space>
      ),
    },
    {
      title: 'Duration',
      dataIndex: 'duration_seconds',
      key: 'duration_seconds',
      width: 100,
      render: (seconds: number) => <Text>{seconds}s</Text>,
    },
    {
      title: 'Impact',
      dataIndex: 'impact',
      key: 'impact',
      width: 100,
      render: (impact: string) => (
        <Tag color={getImpactColor(impact)} icon={<ExclamationCircleOutlined />}>
          {impact}
        </Tag>
      ),
    },
    {
      title: 'Action',
      key: 'action',
      width: 100,
      render: (_: any, record: Deadlock) => (
        <Button type="link" size="small" onClick={() => setSelectedDeadlock(record)}>
          View Details
        </Button>
      ),
    },
  ];

  const renderDeadlockVisualization = (deadlock: Deadlock) => {
    return (
      <Card title="Deadlock Visualization" size="small">
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-around',
            alignItems: 'center',
            padding: '40px 20px',
            background: '#f5f5f5',
            borderRadius: 8,
          }}
        >
          {/* Session 1 */}
          <div style={{ textAlign: 'center' }}>
            <div
              style={{
                width: 120,
                height: 120,
                borderRadius: '50%',
                background: '#1890ff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontSize: 18,
                fontWeight: 'bold',
                boxShadow: '0 4px 8px rgba(0,0,0,0.2)',
              }}
            >
              <div>
                <DatabaseOutlined style={{ fontSize: 32 }} />
                <div>SID {deadlock.session1.sid}</div>
              </div>
            </div>
            <div style={{ marginTop: 16 }}>
              <Text strong>{deadlock.session1.username}</Text>
              <br />
              <Text type="secondary" style={{ fontSize: 12 }}>
                {deadlock.session1.machine}
              </Text>
            </div>
          </div>

          {/* Deadlock Arrows */}
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 48, color: '#ff4d4f' }}>
              <WarningOutlined />
            </div>
            <div style={{ marginTop: 8 }}>
              <Text strong style={{ color: '#ff4d4f' }}>
                DEADLOCK
              </Text>
              <br />
              <Text type="secondary" style={{ fontSize: 12 }}>
                {deadlock.deadlock_type}
              </Text>
            </div>
            <div style={{ marginTop: 16 }}>
              <Space direction="vertical" size={4}>
                <div>
                  <Text style={{ fontSize: 24 }}>⇄</Text>
                </div>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  Waiting on<br />each other
                </Text>
              </Space>
            </div>
          </div>

          {/* Session 2 */}
          <div style={{ textAlign: 'center' }}>
            <div
              style={{
                width: 120,
                height: 120,
                borderRadius: '50%',
                background: '#52c41a',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontSize: 18,
                fontWeight: 'bold',
                boxShadow: '0 4px 8px rgba(0,0,0,0.2)',
              }}
            >
              <div>
                <DatabaseOutlined style={{ fontSize: 32 }} />
                <div>SID {deadlock.session2.sid}</div>
              </div>
            </div>
            <div style={{ marginTop: 16 }}>
              <Text strong>{deadlock.session2.username}</Text>
              <br />
              <Text type="secondary" style={{ fontSize: 12 }}>
                {deadlock.session2.machine}
              </Text>
            </div>
          </div>
        </div>
      </Card>
    );
  };

  const renderSessionDetails = (session: Session, sessionNum: number) => {
    return (
      <Card
        title={
          <Space>
            <DatabaseOutlined />
            Session {sessionNum}
          </Space>
        }
        size="small"
      >
        <Descriptions bordered size="small" column={1}>
          <Descriptions.Item label="Session ID (SID)">
            <Text strong>
              {session.sid}:{session.serial}
            </Text>
          </Descriptions.Item>
          <Descriptions.Item label="Username">
            <Tag color="blue">{session.username}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="SQL ID">
            <Button
              type="link"
              size="small"
              style={{ padding: 0, fontFamily: 'monospace' }}
              onClick={() => navigate(`/queries/${session.sql_id}`)}
            >
              {session.sql_id}
            </Button>
          </Descriptions.Item>
          <Descriptions.Item label="Program">{session.program}</Descriptions.Item>
          <Descriptions.Item label="Machine">{session.machine}</Descriptions.Item>
          <Descriptions.Item label="Blocking Resource">
            <Text code>{session.blocking_resource}</Text>
          </Descriptions.Item>
        </Descriptions>
      </Card>
    );
  };

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          {/* Header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <Title level={2}>
                <WarningOutlined style={{ color: '#ff4d4f' }} /> Deadlock Detection
              </Title>
              <Text type="secondary">
                Monitor and analyze database deadlocks to identify resource contention issues
              </Text>
            </div>
            <Button icon={<ReloadOutlined />} onClick={fetchDeadlocks} loading={loading}>
              Refresh
            </Button>
          </div>

          {error && (
            <Alert
              message="Error"
              description={error}
              type="error"
              closable
              onClose={() => setError(null)}
            />
          )}

          {/* Info Alert */}
          <Alert
            message="About Deadlocks"
            description="A deadlock occurs when two or more sessions are waiting for resources held by each other, creating a circular dependency. Oracle automatically detects deadlocks and resolves them by rolling back one of the sessions."
            type="info"
            showIcon
            icon={<InfoCircleOutlined />}
          />

          {loading ? (
            <div style={{ textAlign: 'center', padding: 60 }}>
              <Spin size="large" tip="Loading deadlocks..." />
            </div>
          ) : deadlocks.length === 0 ? (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description={
                <Space direction="vertical">
                  <CheckCircleOutlined style={{ fontSize: 48, color: '#52c41a' }} />
                  <Title level={4}>No Deadlocks Detected</Title>
                  <Text type="secondary">
                    Great news! No deadlocks have been detected in your database recently.
                  </Text>
                </Space>
              }
            />
          ) : (
            <>
              {/* Deadlocks Table */}
              <Card title={`Detected Deadlocks (${deadlocks.length})`} size="small">
                <Table
                  columns={columns}
                  dataSource={deadlocks}
                  rowKey="deadlock_id"
                  pagination={false}
                  size="small"
                  onRow={(record) => ({
                    onClick: () => setSelectedDeadlock(record),
                    style: {
                      cursor: 'pointer',
                      background:
                        selectedDeadlock?.deadlock_id === record.deadlock_id
                          ? '#e6f7ff'
                          : 'transparent',
                    },
                  })}
                />
              </Card>

              {/* Selected Deadlock Details */}
              {selectedDeadlock && (
                <>
                  <Divider />
                  <Title level={3}>
                    Deadlock #{selectedDeadlock.deadlock_id} Details
                  </Title>

                  {/* Visualization */}
                  {renderDeadlockVisualization(selectedDeadlock)}

                  {/* Deadlock Information */}
                  <Card title="Deadlock Information" size="small">
                    <Descriptions bordered size="small" column={2}>
                      <Descriptions.Item label="Deadlock ID">
                        <Text strong>#{selectedDeadlock.deadlock_id}</Text>
                      </Descriptions.Item>
                      <Descriptions.Item label="Detected Time">
                        <Space>
                          <ClockCircleOutlined />
                          {new Date(selectedDeadlock.detected_time).toLocaleString()}
                        </Space>
                      </Descriptions.Item>
                      <Descriptions.Item label="Deadlock Type">
                        <Tag color="purple">{selectedDeadlock.deadlock_type}</Tag>
                      </Descriptions.Item>
                      <Descriptions.Item label="Resource Type">
                        <Tag color="blue">{selectedDeadlock.resource_type}</Tag>
                      </Descriptions.Item>
                      <Descriptions.Item label="Duration">
                        <Text>
                          <ThunderboltOutlined /> {selectedDeadlock.duration_seconds} seconds
                        </Text>
                      </Descriptions.Item>
                      <Descriptions.Item label="Impact">
                        <Tag
                          color={getImpactColor(selectedDeadlock.impact)}
                          icon={<ExclamationCircleOutlined />}
                        >
                          {selectedDeadlock.impact}
                        </Tag>
                      </Descriptions.Item>
                    </Descriptions>
                  </Card>

                  {/* Session Details */}
                  <Row gutter={16}>
                    <Col span={12}>
                      {renderSessionDetails(selectedDeadlock.session1, 1)}
                    </Col>
                    <Col span={12}>
                      {renderSessionDetails(selectedDeadlock.session2, 2)}
                    </Col>
                  </Row>

                  {/* Resolution */}
                  <Card title="Resolution" size="small">
                    <Alert
                      message="Automatic Resolution"
                      description={selectedDeadlock.resolution}
                      type="success"
                      showIcon
                      icon={<CheckCircleOutlined />}
                    />
                  </Card>

                  {/* Recommendations */}
                  <Card title="Prevention Recommendations" size="small">
                    <Timeline
                      items={[
                        {
                          dot: <InfoCircleOutlined style={{ fontSize: 16 }} />,
                          children: (
                            <div>
                              <Text strong>Consistent Locking Order</Text>
                              <Paragraph type="secondary">
                                Ensure all sessions access resources in the same order to prevent
                                circular dependencies.
                              </Paragraph>
                            </div>
                          ),
                        },
                        {
                          dot: <InfoCircleOutlined style={{ fontSize: 16 }} />,
                          children: (
                            <div>
                              <Text strong>Keep Transactions Short</Text>
                              <Paragraph type="secondary">
                                Minimize transaction duration to reduce lock holding time and
                                deadlock probability.
                              </Paragraph>
                            </div>
                          ),
                        },
                        {
                          dot: <InfoCircleOutlined style={{ fontSize: 16 }} />,
                          children: (
                            <div>
                              <Text strong>Use Lower Isolation Levels</Text>
                              <Paragraph type="secondary">
                                Consider using READ COMMITTED instead of SERIALIZABLE if
                                application logic permits.
                              </Paragraph>
                            </div>
                          ),
                        },
                        {
                          dot: <InfoCircleOutlined style={{ fontSize: 16 }} />,
                          children: (
                            <div>
                              <Text strong>Implement Retry Logic</Text>
                              <Paragraph type="secondary">
                                Add application-level retry logic to handle deadlock exceptions
                                (ORA-00060) gracefully.
                              </Paragraph>
                            </div>
                          ),
                        },
                      ]}
                    />
                  </Card>
                </>
              )}
            </>
          )}
        </Space>
      </Card>
    </div>
  );
};
