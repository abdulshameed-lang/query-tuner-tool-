import React, { useEffect, useState } from 'react';
import {
  Card,
  Table,
  Button,
  Tag,
  Space,
  Spin,
  Alert,
  Typography,
  Row,
  Col,
  Statistic,
  Badge,
  Descriptions,
  Divider,
  Collapse,
  Empty,
} from 'antd';
import {
  ReloadOutlined,
  BugOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  FireOutlined,
  InfoCircleOutlined,
  CodeOutlined,
  SafetyOutlined,
} from '@ant-design/icons';
import { oracleService } from '../services/oracleService';

const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;

interface Bug {
  bug_number: string;
  title: string;
  severity: string;
  category: string;
  description: string;
  workaround: string;
  affected_versions: string[];
  affected_sql_ids: string[];
  confidence: number;
  detection_signals: string[];
}

export const BugDetectionPage: React.FC = () => {
  const [bugs, setBugs] = useState<Bug[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchBugs();
  }, []);

  const fetchBugs = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await oracleService.detectBugs();
      setBugs(data || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch bugs');
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity.toUpperCase()) {
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

  const getSeverityIcon = (severity: string) => {
    switch (severity.toUpperCase()) {
      case 'CRITICAL':
        return <FireOutlined style={{ color: '#cf1322' }} />;
      case 'HIGH':
        return <WarningOutlined style={{ color: '#fa8c16' }} />;
      case 'MEDIUM':
        return <InfoCircleOutlined style={{ color: '#faad14' }} />;
      case 'LOW':
        return <CheckCircleOutlined style={{ color: '#1890ff' }} />;
      default:
        return <BugOutlined />;
    }
  };

  const getCategoryColor = (category: string) => {
    const colors: { [key: string]: string } = {
      OPTIMIZER: 'purple',
      PERFORMANCE: 'orange',
      EXECUTION: 'red',
      PARSING: 'blue',
      STORAGE: 'cyan',
      NETWORK: 'geekblue',
      SECURITY: 'magenta',
    };
    return colors[category.toUpperCase()] || 'default';
  };

  // Calculate statistics
  const criticalCount = bugs.filter((b) => b.severity === 'CRITICAL').length;
  const highCount = bugs.filter((b) => b.severity === 'HIGH').length;
  const mediumCount = bugs.filter((b) => b.severity === 'MEDIUM').length;
  const lowCount = bugs.filter((b) => b.severity === 'LOW').length;

  const affectedSqlCount = new Set(bugs.flatMap((b) => b.affected_sql_ids)).size;

  const columns = [
    {
      title: 'Bug Number',
      dataIndex: 'bug_number',
      key: 'bug_number',
      width: 120,
      render: (bugNumber: string) => (
        <Text strong style={{ fontFamily: 'monospace', color: '#1890ff' }}>
          #{bugNumber}
        </Text>
      ),
    },
    {
      title: 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      width: 120,
      filters: [
        { text: 'Critical', value: 'CRITICAL' },
        { text: 'High', value: 'HIGH' },
        { text: 'Medium', value: 'MEDIUM' },
        { text: 'Low', value: 'LOW' },
      ],
      onFilter: (value: any, record: Bug) => record.severity === value,
      render: (severity: string) => (
        <Tag color={getSeverityColor(severity)} icon={getSeverityIcon(severity)}>
          {severity}
        </Tag>
      ),
    },
    {
      title: 'Category',
      dataIndex: 'category',
      key: 'category',
      width: 130,
      filters: Array.from(new Set(bugs.map((b) => b.category))).map((cat) => ({
        text: cat,
        value: cat,
      })),
      onFilter: (value: any, record: Bug) => record.category === value,
      render: (category: string) => (
        <Tag color={getCategoryColor(category)}>{category}</Tag>
      ),
    },
    {
      title: 'Title',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
      render: (title: string) => <Text strong>{title}</Text>,
    },
    {
      title: 'Confidence',
      dataIndex: 'confidence',
      key: 'confidence',
      width: 120,
      sorter: (a: Bug, b: Bug) => a.confidence - b.confidence,
      render: (confidence: number) => (
        <Tag color={confidence > 0.8 ? 'green' : confidence > 0.6 ? 'gold' : 'orange'}>
          {(confidence * 100).toFixed(0)}%
        </Tag>
      ),
    },
    {
      title: 'Affected SQLs',
      dataIndex: 'affected_sql_ids',
      key: 'affected_sql_ids',
      width: 120,
      render: (sqlIds: string[]) => (
        <Badge
          count={sqlIds.length}
          style={{ backgroundColor: '#1890ff' }}
          showZero
        />
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <Title level={2}>
                <BugOutlined /> Bug Detection
              </Title>
              <Text type="secondary">
                Detect known Oracle bugs affecting your database and get workarounds
              </Text>
            </div>
            <Button
              icon={<ReloadOutlined />}
              onClick={fetchBugs}
              loading={loading}
              type="primary"
            >
              Scan for Bugs
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

          {loading ? (
            <div style={{ textAlign: 'center', padding: 60 }}>
              <Spin size="large" tip="Scanning for known bugs..." />
            </div>
          ) : bugs.length === 0 ? (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description={
                <Space direction="vertical">
                  <CheckCircleOutlined style={{ fontSize: 48, color: '#52c41a' }} />
                  <Title level={4}>No Bugs Detected</Title>
                  <Text type="secondary">
                    Great! No known Oracle bugs were detected in your database.
                  </Text>
                </Space>
              }
            />
          ) : (
            <>
              {/* Summary Statistics */}
              <Alert
                message="Bug Scan Results"
                description={`Found ${bugs.length} potential bug${bugs.length !== 1 ? 's' : ''} affecting your database. Review the details below and apply recommended workarounds.`}
                type="warning"
                showIcon
                icon={<WarningOutlined />}
              />

              <Card title="Summary" size="small">
                <Row gutter={16}>
                  <Col span={6}>
                    <Statistic
                      title="Total Bugs Detected"
                      value={bugs.length}
                      prefix={<BugOutlined />}
                      valueStyle={{ color: '#fa8c16' }}
                    />
                  </Col>
                  <Col span={6}>
                    <Statistic
                      title="Critical"
                      value={criticalCount}
                      prefix={<FireOutlined />}
                      valueStyle={{ color: '#cf1322' }}
                    />
                  </Col>
                  <Col span={6}>
                    <Statistic
                      title="High Priority"
                      value={highCount}
                      prefix={<WarningOutlined />}
                      valueStyle={{ color: '#fa8c16' }}
                    />
                  </Col>
                  <Col span={6}>
                    <Statistic
                      title="Affected Queries"
                      value={affectedSqlCount}
                      prefix={<CodeOutlined />}
                      valueStyle={{ color: '#1890ff' }}
                    />
                  </Col>
                </Row>
              </Card>

              <Divider />

              {/* Bug Details Table */}
              <div>
                <Title level={4}>Detected Bugs</Title>
                <Text type="secondary" style={{ display: 'block', marginBottom: 16 }}>
                  Click on a row to expand and see full details, workarounds, and affected versions.
                </Text>
                <Table
                  columns={columns}
                  dataSource={bugs}
                  rowKey="bug_number"
                  expandable={{
                    expandedRowRender: (bug: Bug) => (
                      <div style={{ padding: '16px', backgroundColor: '#fafafa' }}>
                        <Space direction="vertical" style={{ width: '100%' }} size="middle">
                          {/* Description */}
                          <div>
                            <Title level={5}>
                              <InfoCircleOutlined /> Description
                            </Title>
                            <Paragraph>{bug.description}</Paragraph>
                          </div>

                          {/* Workaround */}
                          <div>
                            <Title level={5}>
                              <SafetyOutlined /> Workaround
                            </Title>
                            <Alert
                              message="Recommended Action"
                              description={bug.workaround}
                              type="success"
                              showIcon
                            />
                          </div>

                          {/* Details */}
                          <Descriptions bordered size="small" column={2}>
                            <Descriptions.Item label="Bug Number" span={1}>
                              <Text copyable strong style={{ fontFamily: 'monospace' }}>
                                {bug.bug_number}
                              </Text>
                            </Descriptions.Item>
                            <Descriptions.Item label="Detection Confidence" span={1}>
                              <Tag
                                color={
                                  bug.confidence > 0.8
                                    ? 'green'
                                    : bug.confidence > 0.6
                                    ? 'gold'
                                    : 'orange'
                                }
                              >
                                {(bug.confidence * 100).toFixed(0)}%
                              </Tag>
                            </Descriptions.Item>
                            <Descriptions.Item label="Affected Versions" span={2}>
                              <Space wrap>
                                {bug.affected_versions.map((version) => (
                                  <Tag key={version} color="red">
                                    {version}
                                  </Tag>
                                ))}
                              </Space>
                            </Descriptions.Item>
                            <Descriptions.Item label="Detection Signals" span={2}>
                              <Space wrap>
                                {bug.detection_signals.map((signal) => (
                                  <Tag key={signal} color="blue">
                                    {signal}
                                  </Tag>
                                ))}
                              </Space>
                            </Descriptions.Item>
                            <Descriptions.Item label="Affected SQL_IDs" span={2}>
                              {bug.affected_sql_ids.length > 0 ? (
                                <Space wrap>
                                  {bug.affected_sql_ids.map((sqlId) => (
                                    <Tag
                                      key={sqlId}
                                      color="purple"
                                      style={{ fontFamily: 'monospace' }}
                                    >
                                      {sqlId}
                                    </Tag>
                                  ))}
                                </Space>
                              ) : (
                                <Text type="secondary">
                                  General bug (not query-specific)
                                </Text>
                              )}
                            </Descriptions.Item>
                          </Descriptions>
                        </Space>
                      </div>
                    ),
                    expandIcon: ({ expanded, onExpand, record }) => (
                      <Button
                        type="link"
                        onClick={(e) => onExpand(record, e)}
                        size="small"
                      >
                        {expanded ? 'Hide Details' : 'View Details'}
                      </Button>
                    ),
                  }}
                  pagination={{
                    pageSize: 10,
                    showSizeChanger: true,
                    showTotal: (total) => `Total ${total} bugs detected`,
                  }}
                />
              </div>

              {/* Recommendations */}
              <Card
                title={
                  <span>
                    <SafetyOutlined /> Recommended Actions
                  </span>
                }
                size="small"
              >
                <Space direction="vertical" style={{ width: '100%' }} size="middle">
                  {criticalCount > 0 && (
                    <Alert
                      message="Critical Bugs Detected"
                      description={`${criticalCount} critical bug${criticalCount !== 1 ? 's' : ''} found. These can cause data corruption or incorrect results. Apply workarounds immediately and consider patching your Oracle database.`}
                      type="error"
                      showIcon
                      icon={<FireOutlined />}
                    />
                  )}
                  {highCount > 0 && (
                    <Alert
                      message="High Priority Bugs"
                      description={`${highCount} high priority bug${highCount !== 1 ? 's' : ''} detected. These can cause significant performance degradation. Review and apply workarounds.`}
                      type="warning"
                      showIcon
                    />
                  )}
                  <Alert
                    message="Next Steps"
                    description={
                      <ol style={{ paddingLeft: 20, margin: 0 }}>
                        <li>Review each bug's workaround below</li>
                        <li>Apply recommended parameter changes or hints</li>
                        <li>Test affected queries after applying workarounds</li>
                        <li>Plan database patching to permanently fix these issues</li>
                        <li>Monitor for any new bugs after patch application</li>
                      </ol>
                    }
                    type="info"
                    showIcon
                  />
                </Space>
              </Card>
            </>
          )}
        </Space>
      </Card>
    </div>
  );
};
