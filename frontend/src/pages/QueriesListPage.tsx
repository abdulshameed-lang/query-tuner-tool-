import React, { useEffect, useState } from 'react';
import { Card, Table, Button, Tag, Space, Spin, Alert, Typography, Select } from 'antd';
import { ThunderboltOutlined, ReloadOutlined, EyeOutlined } from '@ant-design/icons';
import { oracleService, Query } from '../services/oracleService';
import { useNavigate } from 'react-router-dom';

const { Title, Text } = Typography;
const { Option } = Select;

export const QueriesListPage: React.FC = () => {
  const [queries, setQueries] = useState<Query[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [orderBy, setOrderBy] = useState('elapsed_time');
  const navigate = useNavigate();

  const fetchQueries = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await oracleService.getTopQueries(50, orderBy);
      setQueries(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch queries');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueries();
  }, [orderBy]);

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

  const columns = [
    {
      title: 'SQL ID',
      dataIndex: 'sql_id',
      key: 'sql_id',
      width: 150,
      render: (sqlId: string) => (
        <Button type="link" onClick={() => navigate(`/queries/${sqlId}`)}>
          {sqlId}
        </Button>
      ),
    },
    {
      title: 'SQL Text',
      dataIndex: 'sql_text',
      key: 'sql_text',
      ellipsis: true,
      render: (text: string) => (
        <Text style={{ fontSize: 12, fontFamily: 'monospace' }}>
          {text.substring(0, 100)}...
        </Text>
      ),
    },
    {
      title: 'Elapsed Time',
      dataIndex: 'elapsed_time',
      key: 'elapsed_time',
      width: 120,
      render: (time: number) => <Tag color="red">{formatTime(time)}</Tag>,
    },
    {
      title: 'CPU Time',
      dataIndex: 'cpu_time',
      key: 'cpu_time',
      width: 120,
      render: (time: number) => <Tag color="orange">{formatTime(time)}</Tag>,
    },
    {
      title: 'Executions',
      dataIndex: 'executions',
      key: 'executions',
      width: 100,
      render: (num: number) => formatNumber(num),
    },
    {
      title: 'Disk Reads',
      dataIndex: 'disk_reads',
      key: 'disk_reads',
      width: 120,
      render: (num: number) => formatNumber(num),
    },
    {
      title: 'Buffer Gets',
      dataIndex: 'buffer_gets',
      key: 'buffer_gets',
      width: 120,
      render: (num: number) => formatNumber(num),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 100,
      render: (_: any, record: Query) => (
        <Button
          icon={<EyeOutlined />}
          onClick={() => navigate(`/queries/${record.sql_id}`)}
        >
          Details
        </Button>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <Title level={2}>
                <ThunderboltOutlined /> Query Analysis
              </Title>
              <Text type="secondary">
                Analyze slow queries and identify performance bottlenecks
              </Text>
            </div>
            <Space>
              <Select
                value={orderBy}
                onChange={setOrderBy}
                style={{ width: 200 }}
              >
                <Option value="elapsed_time">Order by Elapsed Time</Option>
                <Option value="cpu_time">Order by CPU Time</Option>
                <Option value="disk_reads">Order by Disk Reads</Option>
                <Option value="executions">Order by Executions</Option>
              </Select>
              <Button
                icon={<ReloadOutlined />}
                onClick={fetchQueries}
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
            <div style={{ textAlign: 'center', padding: 40 }}>
              <Spin size="large" tip="Loading queries from Oracle..." />
            </div>
          ) : (
            <>
              <Alert
                message={`Found ${queries.length} queries`}
                type="info"
                showIcon
              />
              <Table
                columns={columns}
                dataSource={queries}
                rowKey="sql_id"
                pagination={{
                  pageSize: 20,
                  showSizeChanger: true,
                  showTotal: (total) => `Total ${total} queries`,
                }}
                scroll={{ x: 1200 }}
              />
            </>
          )}
        </Space>
      </Card>
    </div>
  );
};
