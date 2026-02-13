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
  Progress,
  Select,
  Divider,
} from 'antd';
import {
  ReloadOutlined,
  ClockCircleOutlined,
  DashboardOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  DatabaseOutlined,
} from '@ant-design/icons';
import { oracleService } from '../services/oracleService';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

interface WaitEvent {
  event: string;
  wait_class: string;
  total_waits: number;
  time_waited: number;
  average_wait: number;
}

interface WaitClassSummary {
  wait_class: string;
  total_events: number;
  total_time: number;
  percentage: number;
}

export const WaitEventsPage: React.FC = () => {
  const [waitEvents, setWaitEvents] = useState<WaitEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [topN, setTopN] = useState(50);

  useEffect(() => {
    fetchWaitEvents();
  }, [topN]);

  const fetchWaitEvents = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await oracleService.getSystemWaitEvents(topN);
      setWaitEvents(data || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch wait events');
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(2)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(2)}K`;
    return num.toLocaleString();
  };

  const getWaitClassColor = (waitClass: string) => {
    const colors: { [key: string]: string } = {
      'User I/O': 'blue',
      'System I/O': 'cyan',
      'Commit': 'green',
      'Idle': 'default',
      'CPU': 'red',
      'Application': 'orange',
      'Concurrency': 'purple',
      'Configuration': 'magenta',
      'Network': 'geekblue',
      'Other': 'gray',
    };
    return colors[waitClass] || 'default';
  };

  const getWaitClassIcon = (waitClass: string) => {
    switch (waitClass) {
      case 'User I/O':
      case 'System I/O':
        return <DatabaseOutlined />;
      case 'CPU':
        return <DashboardOutlined />;
      case 'Application':
      case 'Concurrency':
        return <WarningOutlined />;
      case 'Idle':
        return <CheckCircleOutlined />;
      default:
        return <ClockCircleOutlined />;
    }
  };

  // Calculate wait class summaries
  const calculateWaitClassSummary = (): WaitClassSummary[] => {
    const summaryMap: { [key: string]: WaitClassSummary } = {};
    let totalTime = 0;

    waitEvents.forEach((event) => {
      const waitClass = event.wait_class;
      if (!summaryMap[waitClass]) {
        summaryMap[waitClass] = {
          wait_class: waitClass,
          total_events: 0,
          total_time: 0,
          percentage: 0,
        };
      }
      summaryMap[waitClass].total_events += 1;
      summaryMap[waitClass].total_time += event.time_waited;
      totalTime += event.time_waited;
    });

    // Calculate percentages
    Object.values(summaryMap).forEach((summary) => {
      summary.percentage = totalTime > 0 ? (summary.total_time / totalTime) * 100 : 0;
    });

    return Object.values(summaryMap).sort((a, b) => b.total_time - a.total_time);
  };

  const waitClassSummary = calculateWaitClassSummary();
  const totalWaits = waitEvents.reduce((sum, e) => sum + e.total_waits, 0);
  const totalTimeWaited = waitEvents.reduce((sum, e) => sum + e.time_waited, 0);
  const avgWaitTime =
    totalWaits > 0 ? (totalTimeWaited / totalWaits) * 10 : 0; // Convert to ms

  const columns = [
    {
      title: 'Event',
      dataIndex: 'event',
      key: 'event',
      width: 300,
      sorter: (a: WaitEvent, b: WaitEvent) => a.event.localeCompare(b.event),
      render: (event: string) => (
        <Text strong style={{ fontSize: '13px' }}>
          {event}
        </Text>
      ),
    },
    {
      title: 'Wait Class',
      dataIndex: 'wait_class',
      key: 'wait_class',
      width: 150,
      filters: Array.from(new Set(waitEvents.map((e) => e.wait_class))).map(
        (wc) => ({ text: wc, value: wc })
      ),
      onFilter: (value: any, record: WaitEvent) => record.wait_class === value,
      render: (waitClass: string) => (
        <Tag color={getWaitClassColor(waitClass)} icon={getWaitClassIcon(waitClass)}>
          {waitClass}
        </Tag>
      ),
    },
    {
      title: 'Total Waits',
      dataIndex: 'total_waits',
      key: 'total_waits',
      width: 130,
      sorter: (a: WaitEvent, b: WaitEvent) => a.total_waits - b.total_waits,
      defaultSortOrder: 'descend' as const,
      render: (waits: number) => (
        <Text style={{ fontFamily: 'monospace' }}>{formatNumber(waits)}</Text>
      ),
    },
    {
      title: 'Time Waited (cs)',
      dataIndex: 'time_waited',
      key: 'time_waited',
      width: 150,
      sorter: (a: WaitEvent, b: WaitEvent) => a.time_waited - b.time_waited,
      render: (time: number) => (
        <Text strong style={{ fontFamily: 'monospace', color: '#cf1322' }}>
          {formatNumber(time)}
        </Text>
      ),
    },
    {
      title: 'Avg Wait (ms)',
      dataIndex: 'average_wait',
      key: 'average_wait',
      width: 120,
      sorter: (a: WaitEvent, b: WaitEvent) => a.average_wait - b.average_wait,
      render: (avg: number) => (
        <Text style={{ fontFamily: 'monospace' }}>{avg.toFixed(2)}</Text>
      ),
    },
    {
      title: 'Impact',
      key: 'impact',
      width: 100,
      render: (_: any, record: WaitEvent) => {
        const percentage =
          totalTimeWaited > 0 ? (record.time_waited / totalTimeWaited) * 100 : 0;
        let color = 'green';
        if (percentage > 20) color = 'red';
        else if (percentage > 10) color = 'orange';
        else if (percentage > 5) color = 'gold';

        return <Progress percent={parseFloat(percentage.toFixed(1))} strokeColor={color} />;
      },
    },
  ];

  const getRecommendations = () => {
    const recommendations = [];

    // Check for high I/O waits
    const ioEvents = waitEvents.filter(
      (e) => e.wait_class === 'User I/O' || e.wait_class === 'System I/O'
    );
    const ioTime = ioEvents.reduce((sum, e) => sum + e.time_waited, 0);
    const ioPercentage = totalTimeWaited > 0 ? (ioTime / totalTimeWaited) * 100 : 0;

    if (ioPercentage > 40) {
      recommendations.push({
        severity: 'high',
        title: 'High I/O Wait Time Detected',
        description: `${ioPercentage.toFixed(1)}% of wait time is I/O related. Consider optimizing queries, adding indexes, or upgrading storage.`,
      });
    }

    // Check for concurrency issues
    const concurrencyEvents = waitEvents.filter(
      (e) => e.wait_class === 'Concurrency' || e.wait_class === 'Application'
    );
    const concurrencyTime = concurrencyEvents.reduce((sum, e) => sum + e.time_waited, 0);
    const concurrencyPercentage =
      totalTimeWaited > 0 ? (concurrencyTime / totalTimeWaited) * 100 : 0;

    if (concurrencyPercentage > 20) {
      recommendations.push({
        severity: 'high',
        title: 'Concurrency Issues Detected',
        description: `${concurrencyPercentage.toFixed(1)}% of wait time is due to locks and latches. Review application logic and consider reducing transaction scope.`,
      });
    }

    // Check for log file sync
    const logSyncEvents = waitEvents.filter((e) => e.event.includes('log file sync'));
    if (logSyncEvents.length > 0 && logSyncEvents[0].average_wait > 10) {
      recommendations.push({
        severity: 'medium',
        title: 'Slow Commit Performance',
        description: `Average log file sync wait is ${logSyncEvents[0].average_wait.toFixed(2)}ms. Consider faster storage for redo logs or review commit frequency.`,
      });
    }

    // Check CPU time
    const cpuEvents = waitEvents.filter((e) => e.wait_class === 'CPU');
    const cpuTime = cpuEvents.reduce((sum, e) => sum + e.time_waited, 0);
    const cpuPercentage = totalTimeWaited > 0 ? (cpuTime / totalTimeWaited) * 100 : 0;

    if (cpuPercentage > 60) {
      recommendations.push({
        severity: 'medium',
        title: 'High CPU Usage',
        description: `${cpuPercentage.toFixed(1)}% of database time is CPU. Review SQL execution plans and consider SQL tuning.`,
      });
    }

    if (recommendations.length === 0) {
      recommendations.push({
        severity: 'success',
        title: 'Wait Events Look Healthy',
        description: 'No significant wait event issues detected. System performance appears normal.',
      });
    }

    return recommendations;
  };

  const recommendations = getRecommendations();

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <Title level={2}>
                <ClockCircleOutlined /> Wait Events Analysis
              </Title>
              <Text type="secondary">
                System-wide wait events showing database bottlenecks and performance issues
              </Text>
            </div>
            <Space>
              <Select value={topN} onChange={setTopN} style={{ width: 150 }}>
                <Option value={20}>Top 20 Events</Option>
                <Option value={50}>Top 50 Events</Option>
                <Option value={100}>Top 100 Events</Option>
              </Select>
              <Button
                icon={<ReloadOutlined />}
                onClick={fetchWaitEvents}
                loading={loading}
              >
                Refresh
              </Button>
            </Space>
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
              <Spin size="large" tip="Loading wait events..." />
            </div>
          ) : (
            <>
              {/* Summary Statistics */}
              <Card title="Summary Statistics" size="small">
                <Row gutter={16}>
                  <Col span={6}>
                    <Statistic
                      title="Total Wait Events"
                      value={waitEvents.length}
                      prefix={<ClockCircleOutlined />}
                    />
                  </Col>
                  <Col span={6}>
                    <Statistic
                      title="Total Waits"
                      value={formatNumber(totalWaits)}
                      prefix={<DatabaseOutlined />}
                    />
                  </Col>
                  <Col span={6}>
                    <Statistic
                      title="Total Time Waited"
                      value={`${formatNumber(totalTimeWaited)} cs`}
                      valueStyle={{ color: '#cf1322' }}
                    />
                  </Col>
                  <Col span={6}>
                    <Statistic
                      title="Avg Wait Time"
                      value={`${avgWaitTime.toFixed(2)} ms`}
                      valueStyle={{ color: '#fa8c16' }}
                    />
                  </Col>
                </Row>
              </Card>

              {/* Wait Class Breakdown */}
              <Card title="Wait Class Breakdown" size="small">
                <Row gutter={[16, 16]}>
                  {waitClassSummary.map((summary) => (
                    <Col span={12} key={summary.wait_class}>
                      <Card size="small" style={{ backgroundColor: '#fafafa' }}>
                        <Space direction="vertical" style={{ width: '100%' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <Space>
                              {getWaitClassIcon(summary.wait_class)}
                              <Text strong>{summary.wait_class}</Text>
                            </Space>
                            <Tag color={getWaitClassColor(summary.wait_class)}>
                              {summary.total_events} events
                            </Tag>
                          </div>
                          <div>
                            <Text type="secondary" style={{ fontSize: 12 }}>
                              Total Time: {formatNumber(summary.total_time)} cs
                            </Text>
                          </div>
                          <Progress
                            percent={parseFloat(summary.percentage.toFixed(1))}
                            strokeColor={
                              summary.percentage > 30
                                ? '#cf1322'
                                : summary.percentage > 15
                                ? '#fa8c16'
                                : '#52c41a'
                            }
                          />
                        </Space>
                      </Card>
                    </Col>
                  ))}
                </Row>
              </Card>

              {/* Recommendations */}
              <Card title="Recommendations" size="small">
                <Space direction="vertical" style={{ width: '100%' }} size="middle">
                  {recommendations.map((rec, index) => (
                    <Alert
                      key={index}
                      message={rec.title}
                      description={rec.description}
                      type={
                        rec.severity === 'high'
                          ? 'error'
                          : rec.severity === 'medium'
                          ? 'warning'
                          : rec.severity === 'success'
                          ? 'success'
                          : 'info'
                      }
                      showIcon
                      icon={
                        rec.severity === 'success' ? (
                          <CheckCircleOutlined />
                        ) : (
                          <WarningOutlined />
                        )
                      }
                    />
                  ))}
                </Space>
              </Card>

              <Divider />

              {/* Wait Events Table */}
              <div>
                <Title level={4}>All Wait Events</Title>
                <Text type="secondary" style={{ display: 'block', marginBottom: 16 }}>
                  Click on column headers to sort. Use filters to narrow down by wait class.
                </Text>
                <Table
                  columns={columns}
                  dataSource={waitEvents}
                  rowKey="event"
                  pagination={{
                    pageSize: 20,
                    showSizeChanger: true,
                    showTotal: (total) => `Total ${total} wait events`,
                  }}
                  scroll={{ x: 1200 }}
                  size="small"
                />
              </div>
            </>
          )}
        </Space>
      </Card>
    </div>
  );
};
