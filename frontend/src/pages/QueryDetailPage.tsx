import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Spin,
  Alert,
  Typography,
  Descriptions,
  Tag,
  Space,
  Button,
  Tabs,
  Table,
  Progress,
  Statistic,
  Row,
  Col,
  Divider,
} from 'antd';
import {
  ArrowLeftOutlined,
  ThunderboltOutlined,
  ClockCircleOutlined,
  DatabaseOutlined,
  BugOutlined,
  CheckCircleOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import { oracleService } from '../services/oracleService';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;

interface QueryDetails {
  sql_id: string;
  sql_text: string;
  elapsed_time: number;
  cpu_time: number;
  executions: number;
  disk_reads: number;
  buffer_gets: number;
  rows_processed: number;
  first_load_time: string;
  last_active_time: string;
  plan_hash_value: number;
  parsing_schema_name: string;
}

interface ExecutionPlan {
  operations: any[];
  total_cost: number;
  estimated_rows: number;
}

interface WaitEvent {
  event: string;
  wait_class: string;
  total_waits: number;
  time_waited: number;
  average_wait: number;
}

interface Recommendation {
  type: string;
  priority: string;
  title: string;
  description: string;
  estimated_benefit: string;
  sql?: string;
}

export const QueryDetailPage: React.FC = () => {
  const { sqlId } = useParams<{ sqlId: string }>();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [queryDetails, setQueryDetails] = useState<QueryDetails | null>(null);
  const [executionPlan, setExecutionPlan] = useState<ExecutionPlan | null>(null);
  const [waitEvents, setWaitEvents] = useState<WaitEvent[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);

  useEffect(() => {
    fetchQueryDetails();
  }, [sqlId]);

  const fetchQueryDetails = async () => {
    if (!sqlId) return;

    setLoading(true);
    setError(null);

    try {
      // Fetch all data in parallel
      const [detailsRes, planRes, eventsRes, recsRes] = await Promise.allSettled([
        oracleService.getQueryDetails(sqlId),
        oracleService.getExecutionPlan(sqlId),
        oracleService.getSystemWaitEvents(20),
        oracleService.getRecommendations(sqlId),
      ]);

      // Handle query details
      if (detailsRes.status === 'fulfilled') {
        setQueryDetails(detailsRes.value.query || detailsRes.value);
      }

      // Handle execution plan
      if (planRes.status === 'fulfilled') {
        setExecutionPlan(planRes.value.plan || planRes.value);
      }

      // Handle wait events
      if (eventsRes.status === 'fulfilled') {
        setWaitEvents(eventsRes.value.events || eventsRes.value || []);
      }

      // Handle recommendations
      if (recsRes.status === 'fulfilled') {
        setRecommendations(recsRes.value.recommendations || []);
      }

    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch query details');
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (microseconds: number) => {
    const seconds = microseconds / 1000000;
    if (seconds < 1) return `${(seconds * 1000).toFixed(2)}ms`;
    if (seconds < 60) return `${seconds.toFixed(2)}s`;
    return `${(seconds / 60).toFixed(2)}m`;
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(2)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(2)}K`;
    return num.toString();
  };

  const getPriorityColor = (priority: string) => {
    switch (priority.toUpperCase()) {
      case 'CRITICAL':
        return 'red';
      case 'HIGH':
        return 'orange';
      case 'MEDIUM':
        return 'gold';
      case 'LOW':
        return 'blue';
      default:
        return 'default';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type.toUpperCase()) {
      case 'INDEX':
        return <DatabaseOutlined />;
      case 'SQL_REWRITE':
        return <ThunderboltOutlined />;
      case 'STATISTICS':
        return <CheckCircleOutlined />;
      default:
        return <WarningOutlined />;
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px' }}>
        <Spin size="large" tip="Loading query details..." />
      </div>
    );
  }

  if (error || !queryDetails) {
    return (
      <div style={{ padding: '24px' }}>
        <Button
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/queries')}
          style={{ marginBottom: '16px' }}
        >
          Back to Queries
        </Button>
        <Alert
          message="Error"
          description={error || 'Query not found'}
          type="error"
          showIcon
        />
      </div>
    );
  }

  const executionPlanColumns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 60,
    },
    {
      title: 'Operation',
      dataIndex: 'operation',
      key: 'operation',
      render: (op: string, record: any) => (
        <span style={{ paddingLeft: record.parent_id ? record.parent_id * 20 : 0 }}>
          {op} {record.options && `(${record.options})`}
        </span>
      ),
    },
    {
      title: 'Object Name',
      dataIndex: 'object_name',
      key: 'object_name',
    },
    {
      title: 'Cost',
      dataIndex: 'cost',
      key: 'cost',
      render: (cost: number) => cost?.toLocaleString() || '-',
    },
    {
      title: 'Cardinality',
      dataIndex: 'cardinality',
      key: 'cardinality',
      render: (card: number) => formatNumber(card || 0),
    },
    {
      title: 'Bytes',
      dataIndex: 'bytes',
      key: 'bytes',
      render: (bytes: number) => formatNumber(bytes || 0),
    },
  ];

  const waitEventsColumns = [
    {
      title: 'Event',
      dataIndex: 'event',
      key: 'event',
    },
    {
      title: 'Wait Class',
      dataIndex: 'wait_class',
      key: 'wait_class',
      render: (waitClass: string) => <Tag color="blue">{waitClass}</Tag>,
    },
    {
      title: 'Total Waits',
      dataIndex: 'total_waits',
      key: 'total_waits',
      render: (waits: number) => formatNumber(waits),
    },
    {
      title: 'Time Waited (cs)',
      dataIndex: 'time_waited',
      key: 'time_waited',
      render: (time: number) => formatNumber(time),
    },
    {
      title: 'Avg Wait (ms)',
      dataIndex: 'average_wait',
      key: 'average_wait',
      render: (avg: number) => avg.toFixed(2),
    },
  ];

  const cpuPercentage = queryDetails.elapsed_time > 0
    ? (queryDetails.cpu_time / queryDetails.elapsed_time) * 100
    : 0;

  return (
    <div style={{ padding: '24px' }}>
      <Button
        icon={<ArrowLeftOutlined />}
        onClick={() => navigate('/queries')}
        style={{ marginBottom: '16px' }}
      >
        Back to Queries
      </Button>

      <Card>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          {/* Header */}
          <div>
            <Title level={2}>
              <ThunderboltOutlined /> Query Details
            </Title>
            <Space>
              <Tag color="blue" style={{ fontSize: '16px', padding: '4px 12px' }}>
                {queryDetails.sql_id}
              </Tag>
              <Tag color="purple">{queryDetails.parsing_schema_name}</Tag>
              <Text type="secondary">
                Plan Hash: {queryDetails.plan_hash_value}
              </Text>
            </Space>
          </div>

          {/* Performance Metrics */}
          <Card title="Performance Metrics" size="small">
            <Row gutter={16}>
              <Col span={6}>
                <Statistic
                  title="Elapsed Time"
                  value={formatTime(queryDetails.elapsed_time)}
                  prefix={<ClockCircleOutlined />}
                  valueStyle={{ color: '#cf1322' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="CPU Time"
                  value={formatTime(queryDetails.cpu_time)}
                  prefix={<ThunderboltOutlined />}
                  valueStyle={{ color: '#fa8c16' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="Executions"
                  value={formatNumber(queryDetails.executions)}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="Rows Processed"
                  value={formatNumber(queryDetails.rows_processed)}
                />
              </Col>
            </Row>
            <Divider />
            <Row gutter={16}>
              <Col span={6}>
                <Statistic
                  title="Disk Reads"
                  value={formatNumber(queryDetails.disk_reads)}
                  prefix={<DatabaseOutlined />}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="Buffer Gets"
                  value={formatNumber(queryDetails.buffer_gets)}
                />
              </Col>
              <Col span={6}>
                <div>
                  <Text type="secondary">CPU Usage</Text>
                  <div>
                    <Progress
                      percent={parseFloat(cpuPercentage.toFixed(1))}
                      status={cpuPercentage > 80 ? 'exception' : 'normal'}
                    />
                  </div>
                </div>
              </Col>
              <Col span={6}>
                <div>
                  <Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
                    Avg Time/Exec
                  </Text>
                  <Text strong style={{ fontSize: 20 }}>
                    {formatTime(queryDetails.elapsed_time / queryDetails.executions)}
                  </Text>
                </div>
              </Col>
            </Row>
          </Card>

          {/* SQL Text */}
          <Card title="SQL Text" size="small">
            <Paragraph
              copyable
              style={{
                fontFamily: 'monospace',
                fontSize: '13px',
                backgroundColor: '#f5f5f5',
                padding: '12px',
                borderRadius: '4px',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
              }}
            >
              {queryDetails.sql_text}
            </Paragraph>
          </Card>

          {/* Tabs for Execution Plan, Wait Events, Recommendations */}
          <Tabs defaultActiveKey="execution-plan">
            <TabPane tab="Execution Plan" key="execution-plan">
              {executionPlan ? (
                <div>
                  <Space style={{ marginBottom: 16 }}>
                    <Text>
                      <strong>Total Cost:</strong> {executionPlan.total_cost?.toLocaleString()}
                    </Text>
                    <Text>
                      <strong>Estimated Rows:</strong>{' '}
                      {formatNumber(executionPlan.estimated_rows)}
                    </Text>
                  </Space>
                  <Table
                    columns={executionPlanColumns}
                    dataSource={executionPlan.operations || []}
                    rowKey="id"
                    pagination={false}
                    size="small"
                    bordered
                  />
                </div>
              ) : (
                <Alert
                  message="No execution plan available"
                  type="info"
                  showIcon
                />
              )}
            </TabPane>

            <TabPane tab="Wait Events" key="wait-events">
              {waitEvents.length > 0 ? (
                <Table
                  columns={waitEventsColumns}
                  dataSource={waitEvents}
                  rowKey="event"
                  pagination={{ pageSize: 10 }}
                  size="small"
                />
              ) : (
                <Alert
                  message="No wait events data available"
                  type="info"
                  showIcon
                />
              )}
            </TabPane>

            <TabPane
              tab={
                <span>
                  Recommendations{' '}
                  {recommendations.length > 0 && (
                    <Tag color="red">{recommendations.length}</Tag>
                  )}
                </span>
              }
              key="recommendations"
            >
              {recommendations.length > 0 ? (
                <Space direction="vertical" style={{ width: '100%' }} size="middle">
                  {recommendations.map((rec, index) => (
                    <Card
                      key={index}
                      size="small"
                      title={
                        <Space>
                          {getTypeIcon(rec.type)}
                          <span>{rec.title}</span>
                          <Tag color={getPriorityColor(rec.priority)}>
                            {rec.priority}
                          </Tag>
                        </Space>
                      }
                    >
                      <Paragraph>{rec.description}</Paragraph>
                      {rec.estimated_benefit && (
                        <Alert
                          message={`Estimated Benefit: ${rec.estimated_benefit}`}
                          type="success"
                          showIcon
                          style={{ marginBottom: 12 }}
                        />
                      )}
                      {rec.sql && (
                        <Paragraph
                          copyable
                          style={{
                            fontFamily: 'monospace',
                            fontSize: '12px',
                            backgroundColor: '#f5f5f5',
                            padding: '8px',
                            borderRadius: '4px',
                            marginBottom: 0,
                          }}
                        >
                          {rec.sql}
                        </Paragraph>
                      )}
                    </Card>
                  ))}
                </Space>
              ) : (
                <Alert
                  message="No recommendations at this time"
                  description="This query appears to be performing well!"
                  type="success"
                  showIcon
                  icon={<CheckCircleOutlined />}
                />
              )}
            </TabPane>
          </Tabs>

          {/* Timestamps */}
          <Descriptions size="small" column={2} bordered>
            <Descriptions.Item label="First Load Time">
              {new Date(queryDetails.first_load_time).toLocaleString()}
            </Descriptions.Item>
            <Descriptions.Item label="Last Active Time">
              {new Date(queryDetails.last_active_time).toLocaleString()}
            </Descriptions.Item>
          </Descriptions>
        </Space>
      </Card>
    </div>
  );
};
