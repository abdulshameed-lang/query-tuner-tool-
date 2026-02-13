import React, { useEffect, useState } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Spin,
  Alert,
  Typography,
  Row,
  Col,
  Statistic,
  Select,
  Divider,
  Descriptions,
  Progress,
  Tag,
} from 'antd';
import {
  ReloadOutlined,
  BarChartOutlined,
  ClockCircleOutlined,
  ThunderboltOutlined,
  DatabaseOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import { oracleService } from '../services/oracleService';

const { Title, Text } = Typography;
const { Option } = Select;

interface Snapshot {
  snap_id: number;
  begin_time: string;
  end_time: string;
  startup_time: string;
}

interface AWRReport {
  report_info: {
    db_name: string;
    instance_name: string;
    begin_snap_id: number;
    end_snap_id: number;
    elapsed_time: number;
  };
  top_sql_by_elapsed_time: any[];
  wait_events: any[];
  load_profile: {
    db_time: number;
    db_cpu: number;
    redo_size: number;
    logical_reads: number;
    physical_reads: number;
    user_calls: number;
  };
  efficiency_metrics: {
    buffer_hit_ratio: number;
    library_cache_hit_ratio: number;
    soft_parse_ratio: number;
  };
}

export const PerformanceReportsPage: React.FC = () => {
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]);
  const [report, setReport] = useState<AWRReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [daysBack, setDaysBack] = useState(7);
  const [beginSnapId, setBeginSnapId] = useState<number | null>(null);
  const [endSnapId, setEndSnapId] = useState<number | null>(null);

  useEffect(() => {
    fetchSnapshots();
  }, [daysBack]);

  const fetchSnapshots = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await oracleService.getAWRSnapshots(daysBack);
      setSnapshots(data || []);

      // Auto-select last 2 snapshots for convenience
      if (data && data.length >= 2) {
        setBeginSnapId(data[data.length - 2].snap_id);
        setEndSnapId(data[data.length - 1].snap_id);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch AWR snapshots');
    } finally {
      setLoading(false);
    }
  };

  const generateReport = async () => {
    if (!beginSnapId || !endSnapId) {
      setError('Please select both begin and end snapshots');
      return;
    }

    if (beginSnapId >= endSnapId) {
      setError('Begin snapshot must be before end snapshot');
      return;
    }

    setGeneratingReport(true);
    setError(null);
    try {
      const reportData = await oracleService.generateAWRReport(beginSnapId, endSnapId);
      setReport(reportData);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate AWR report');
    } finally {
      setGeneratingReport(false);
    }
  };

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours}h ${minutes}m ${secs}s`;
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000000) return `${(num / 1000000000).toFixed(2)}B`;
    if (num >= 1000000) return `${(num / 1000000).toFixed(2)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(2)}K`;
    return num.toLocaleString();
  };

  const snapshotColumns = [
    {
      title: 'Snapshot ID',
      dataIndex: 'snap_id',
      key: 'snap_id',
      width: 120,
    },
    {
      title: 'Begin Time',
      dataIndex: 'begin_time',
      key: 'begin_time',
      render: (time: string) => new Date(time).toLocaleString(),
    },
    {
      title: 'End Time',
      dataIndex: 'end_time',
      key: 'end_time',
      render: (time: string) => new Date(time).toLocaleString(),
    },
  ];

  const topSqlColumns = [
    {
      title: 'SQL ID',
      dataIndex: 'sql_id',
      key: 'sql_id',
      width: 150,
      render: (sqlId: string) => (
        <Text style={{ fontFamily: 'monospace', color: '#1890ff' }}>{sqlId}</Text>
      ),
    },
    {
      title: 'Elapsed Time',
      dataIndex: 'elapsed_time',
      key: 'elapsed_time',
      width: 130,
      render: (time: number) => (
        <Tag color="red">{formatTime(time / 1000000)}</Tag>
      ),
    },
    {
      title: 'Executions',
      dataIndex: 'executions',
      key: 'executions',
      width: 110,
      render: (num: number) => formatNumber(num),
    },
    {
      title: 'SQL Text',
      dataIndex: 'sql_text',
      key: 'sql_text',
      ellipsis: true,
      render: (text: string) => (
        <Text style={{ fontSize: 12, fontFamily: 'monospace' }}>
          {text.substring(0, 80)}...
        </Text>
      ),
    },
  ];

  const waitEventsColumns = [
    {
      title: 'Event',
      dataIndex: 'event',
      key: 'event',
      width: 250,
    },
    {
      title: 'Wait Class',
      dataIndex: 'wait_class',
      key: 'wait_class',
      width: 130,
      render: (waitClass: string) => <Tag color="blue">{waitClass}</Tag>,
    },
    {
      title: 'Total Waits',
      dataIndex: 'total_waits',
      key: 'total_waits',
      width: 120,
      render: (waits: number) => formatNumber(waits),
    },
    {
      title: 'Time Waited',
      dataIndex: 'time_waited',
      key: 'time_waited',
      width: 130,
      render: (time: number) => <Text strong>{formatNumber(time)} cs</Text>,
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <Title level={2}>
                <BarChartOutlined /> Performance Reports (AWR)
              </Title>
              <Text type="secondary">
                Automatic Workload Repository reports for historical performance analysis
              </Text>
            </div>
            <Space>
              <Select value={daysBack} onChange={setDaysBack} style={{ width: 150 }}>
                <Option value={1}>Last 1 Day</Option>
                <Option value={3}>Last 3 Days</Option>
                <Option value={7}>Last 7 Days</Option>
                <Option value={14}>Last 14 Days</Option>
                <Option value={30}>Last 30 Days</Option>
              </Select>
              <Button icon={<ReloadOutlined />} onClick={fetchSnapshots} loading={loading}>
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
              <Spin size="large" tip="Loading AWR snapshots..." />
            </div>
          ) : (
            <>
              {/* Snapshot Selection */}
              <Card title="Select Report Period" size="small">
                <Space direction="vertical" style={{ width: '100%' }} size="middle">
                  <Alert
                    message="AWR Report Configuration"
                    description="Select begin and end snapshots to generate an AWR report. The report will show performance metrics for the period between these snapshots."
                    type="info"
                    showIcon
                  />
                  <Row gutter={16}>
                    <Col span={8}>
                      <Space direction="vertical" style={{ width: '100%' }}>
                        <Text strong>Begin Snapshot:</Text>
                        <Select
                          value={beginSnapId}
                          onChange={setBeginSnapId}
                          style={{ width: '100%' }}
                          placeholder="Select begin snapshot"
                        >
                          {snapshots.map((snap) => (
                            <Option key={snap.snap_id} value={snap.snap_id}>
                              #{snap.snap_id} - {new Date(snap.begin_time).toLocaleString()}
                            </Option>
                          ))}
                        </Select>
                      </Space>
                    </Col>
                    <Col span={8}>
                      <Space direction="vertical" style={{ width: '100%' }}>
                        <Text strong>End Snapshot:</Text>
                        <Select
                          value={endSnapId}
                          onChange={setEndSnapId}
                          style={{ width: '100%' }}
                          placeholder="Select end snapshot"
                        >
                          {snapshots.map((snap) => (
                            <Option key={snap.snap_id} value={snap.snap_id}>
                              #{snap.snap_id} - {new Date(snap.end_time).toLocaleString()}
                            </Option>
                          ))}
                        </Select>
                      </Space>
                    </Col>
                    <Col span={8}>
                      <Space direction="vertical" style={{ width: '100%' }}>
                        <Text strong>&nbsp;</Text>
                        <Button
                          type="primary"
                          icon={<FileTextOutlined />}
                          onClick={generateReport}
                          loading={generatingReport}
                          disabled={!beginSnapId || !endSnapId}
                          block
                          size="large"
                        >
                          Generate AWR Report
                        </Button>
                      </Space>
                    </Col>
                  </Row>
                </Space>
              </Card>

              {/* Available Snapshots Table */}
              <Card title="Available Snapshots" size="small">
                <Alert
                  message={`Found ${snapshots.length} snapshots`}
                  type="info"
                  showIcon
                  style={{ marginBottom: 16 }}
                />
                <Table
                  columns={snapshotColumns}
                  dataSource={snapshots}
                  rowKey="snap_id"
                  pagination={{ pageSize: 10, showSizeChanger: true }}
                  size="small"
                />
              </Card>

              {/* AWR Report Results */}
              {report && (
                <>
                  <Divider />
                  <Title level={3}>
                    <FileTextOutlined /> AWR Report Results
                  </Title>

                  {/* Report Info */}
                  <Card title="Report Information" size="small">
                    <Descriptions bordered size="small" column={2}>
                      <Descriptions.Item label="Database Name">
                        <Tag color="blue">{report.report_info.db_name}</Tag>
                      </Descriptions.Item>
                      <Descriptions.Item label="Instance Name">
                        <Tag color="purple">{report.report_info.instance_name}</Tag>
                      </Descriptions.Item>
                      <Descriptions.Item label="Begin Snapshot">
                        #{report.report_info.begin_snap_id}
                      </Descriptions.Item>
                      <Descriptions.Item label="End Snapshot">
                        #{report.report_info.end_snap_id}
                      </Descriptions.Item>
                      <Descriptions.Item label="Elapsed Time" span={2}>
                        <Text strong>{formatTime(report.report_info.elapsed_time)}</Text>
                      </Descriptions.Item>
                    </Descriptions>
                  </Card>

                  {/* Load Profile */}
                  <Card title="Load Profile" size="small">
                    <Row gutter={16}>
                      <Col span={8}>
                        <Statistic
                          title="DB Time"
                          value={formatTime(report.load_profile.db_time)}
                          prefix={<ClockCircleOutlined />}
                        />
                      </Col>
                      <Col span={8}>
                        <Statistic
                          title="DB CPU"
                          value={formatTime(report.load_profile.db_cpu)}
                          prefix={<ThunderboltOutlined />}
                          valueStyle={{ color: '#fa8c16' }}
                        />
                      </Col>
                      <Col span={8}>
                        <Statistic
                          title="Redo Size"
                          value={formatNumber(report.load_profile.redo_size)}
                          prefix={<DatabaseOutlined />}
                        />
                      </Col>
                    </Row>
                    <Divider />
                    <Row gutter={16}>
                      <Col span={8}>
                        <Statistic
                          title="Logical Reads"
                          value={formatNumber(report.load_profile.logical_reads)}
                        />
                      </Col>
                      <Col span={8}>
                        <Statistic
                          title="Physical Reads"
                          value={formatNumber(report.load_profile.physical_reads)}
                        />
                      </Col>
                      <Col span={8}>
                        <Statistic
                          title="User Calls"
                          value={formatNumber(report.load_profile.user_calls)}
                        />
                      </Col>
                    </Row>
                  </Card>

                  {/* Efficiency Metrics */}
                  <Card title="Efficiency Metrics" size="small">
                    <Row gutter={16}>
                      <Col span={8}>
                        <Space direction="vertical" style={{ width: '100%' }}>
                          <Text strong>Buffer Hit Ratio</Text>
                          <Progress
                            percent={parseFloat(report.efficiency_metrics.buffer_hit_ratio.toFixed(1))}
                            status={
                              report.efficiency_metrics.buffer_hit_ratio > 95
                                ? 'success'
                                : report.efficiency_metrics.buffer_hit_ratio > 90
                                ? 'normal'
                                : 'exception'
                            }
                          />
                          <Text type="secondary">
                            {report.efficiency_metrics.buffer_hit_ratio > 95
                              ? '✓ Excellent'
                              : report.efficiency_metrics.buffer_hit_ratio > 90
                              ? '⚠ Good'
                              : '✗ Needs improvement'}
                          </Text>
                        </Space>
                      </Col>
                      <Col span={8}>
                        <Space direction="vertical" style={{ width: '100%' }}>
                          <Text strong>Library Cache Hit Ratio</Text>
                          <Progress
                            percent={parseFloat(
                              report.efficiency_metrics.library_cache_hit_ratio.toFixed(1)
                            )}
                            status={
                              report.efficiency_metrics.library_cache_hit_ratio > 95
                                ? 'success'
                                : 'normal'
                            }
                          />
                          <Text type="secondary">
                            {report.efficiency_metrics.library_cache_hit_ratio > 95
                              ? '✓ Excellent'
                              : '⚠ Good'}
                          </Text>
                        </Space>
                      </Col>
                      <Col span={8}>
                        <Space direction="vertical" style={{ width: '100%' }}>
                          <Text strong>Soft Parse Ratio</Text>
                          <Progress
                            percent={parseFloat(
                              report.efficiency_metrics.soft_parse_ratio.toFixed(1)
                            )}
                            status={
                              report.efficiency_metrics.soft_parse_ratio > 95
                                ? 'success'
                                : 'normal'
                            }
                          />
                          <Text type="secondary">
                            {report.efficiency_metrics.soft_parse_ratio > 95
                              ? '✓ Excellent'
                              : '⚠ Consider using bind variables'}
                          </Text>
                        </Space>
                      </Col>
                    </Row>
                  </Card>

                  {/* Top SQL */}
                  <Card title="Top SQL by Elapsed Time" size="small">
                    <Table
                      columns={topSqlColumns}
                      dataSource={report.top_sql_by_elapsed_time}
                      rowKey="sql_id"
                      pagination={false}
                      size="small"
                    />
                  </Card>

                  {/* Wait Events */}
                  <Card title="Top Wait Events" size="small">
                    <Table
                      columns={waitEventsColumns}
                      dataSource={report.wait_events}
                      rowKey="event"
                      pagination={false}
                      size="small"
                    />
                  </Card>

                  {/* Success Message */}
                  <Alert
                    message="Report Generated Successfully"
                    description="The AWR report has been generated. Review the metrics above to identify performance bottlenecks and optimization opportunities."
                    type="success"
                    showIcon
                    icon={<CheckCircleOutlined />}
                  />
                </>
              )}
            </>
          )}
        </Space>
      </Card>
    </div>
  );
};
