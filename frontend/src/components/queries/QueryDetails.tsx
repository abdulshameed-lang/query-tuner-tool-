/**
 * QueryDetails component - displays comprehensive query information.
 */

import React from 'react';
import {
  Card,
  Descriptions,
  Typography,
  Space,
  Tag,
  Alert,
  Spin,
  Divider,
  Row,
  Col,
  Statistic,
} from 'antd';
import {
  ClockCircleOutlined,
  ThunderboltOutlined,
  DatabaseOutlined,
  FileTextOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import { useQueryDetail, formatElapsedTime, formatNumber, formatBytes } from '../../api/queries';

const { Title, Text, Paragraph } = Typography;

interface QueryDetailsProps {
  sqlId: string;
}

const QueryDetails: React.FC<QueryDetailsProps> = ({ sqlId }) => {
  const { data, isLoading, isError, error } = useQueryDetail(sqlId);

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '48px' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>
          <Text type="secondary">Loading query details...</Text>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <Alert
        message="Error Loading Query Details"
        description={
          error?.response?.data?.message || error?.message || 'Failed to fetch query details'
        }
        type="error"
        showIcon
        style={{ margin: '24px' }}
      />
    );
  }

  if (!data) {
    return (
      <Alert
        message="Query Not Found"
        description={`No query found with SQL_ID: ${sqlId}`}
        type="warning"
        showIcon
        style={{ margin: '24px' }}
      />
    );
  }

  const query = data.data;

  return (
    <div style={{ padding: '24px' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* Header */}
        <Card>
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            <div>
              <Title level={3} style={{ margin: 0 }}>
                Query Details
              </Title>
              <Space style={{ marginTop: 8 }}>
                <Text code copyable={{ text: query.sql_id }}>
                  {query.sql_id}
                </Text>
                {query.needs_tuning && (
                  <Tag color="red" icon={<WarningOutlined />}>
                    NEEDS TUNING
                  </Tag>
                )}
                <Tag color="blue">{query.parsing_schema_name}</Tag>
              </Space>
            </div>

            {/* SQL Text */}
            <div>
              <Text strong style={{ fontSize: '16px' }}>
                <FileTextOutlined /> SQL Statement
              </Text>
              <Paragraph
                copyable
                style={{
                  backgroundColor: '#f5f5f5',
                  padding: '16px',
                  borderRadius: '4px',
                  fontFamily: 'monospace',
                  fontSize: '13px',
                  marginTop: 12,
                  marginBottom: 0,
                  whiteSpace: 'pre-wrap',
                }}
              >
                {query.sql_text}
              </Paragraph>
            </div>
          </Space>
        </Card>

        {/* Performance Overview */}
        <Card title={<><ThunderboltOutlined /> Performance Overview</>}>
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12} md={6}>
              <Statistic
                title="Impact Score"
                value={query.impact_score}
                precision={2}
                valueStyle={{
                  color: query.impact_score > 50 ? '#cf1322' : query.impact_score > 25 ? '#fa8c16' : '#3f8600',
                }}
              />
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Statistic
                title="Total Elapsed Time"
                value={query.elapsed_time}
                formatter={(value) => formatElapsedTime(value as number)}
                prefix={<ClockCircleOutlined />}
              />
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Statistic
                title="Avg Elapsed Time"
                value={query.avg_elapsed_time}
                formatter={(value) => formatElapsedTime(value as number)}
              />
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Statistic
                title="Executions"
                value={query.executions}
                formatter={(value) => formatNumber(value as number)}
              />
            </Col>
          </Row>
        </Card>

        {/* Execution Metrics */}
        <Card title={<><ClockCircleOutlined /> Execution Metrics</>}>
          <Descriptions bordered size="small" column={{ xs: 1, sm: 2, md: 3 }}>
            <Descriptions.Item label="Total Elapsed Time">
              {formatElapsedTime(query.elapsed_time)}
            </Descriptions.Item>
            <Descriptions.Item label="Avg Elapsed Time">
              {formatElapsedTime(query.avg_elapsed_time)}
            </Descriptions.Item>
            <Descriptions.Item label="CPU Time">
              {formatElapsedTime(query.cpu_time)}
            </Descriptions.Item>
            <Descriptions.Item label="Avg CPU Time">
              {formatElapsedTime(query.avg_cpu_time)}
            </Descriptions.Item>
            <Descriptions.Item label="Executions">{formatNumber(query.executions)}</Descriptions.Item>
            <Descriptions.Item label="Parse Calls">
              {query.parse_calls !== undefined ? formatNumber(query.parse_calls) : 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="Rows Processed">
              {formatNumber(query.rows_processed)}
            </Descriptions.Item>
            <Descriptions.Item label="Fetches">{formatNumber(query.fetches)}</Descriptions.Item>
            <Descriptions.Item label="First Load Time">{query.first_load_time}</Descriptions.Item>
            <Descriptions.Item label="Last Active Time">{query.last_active_time}</Descriptions.Item>
          </Descriptions>
        </Card>

        {/* I/O and Resource Metrics */}
        <Card title={<><DatabaseOutlined /> I/O and Resource Metrics</>}>
          <Descriptions bordered size="small" column={{ xs: 1, sm: 2, md: 3 }}>
            <Descriptions.Item label="Buffer Gets">{formatNumber(query.buffer_gets)}</Descriptions.Item>
            <Descriptions.Item label="Avg Buffer Gets">
              {formatNumber(query.avg_buffer_gets)}
            </Descriptions.Item>
            <Descriptions.Item label="Disk Reads">{formatNumber(query.disk_reads)}</Descriptions.Item>
            <Descriptions.Item label="Avg Disk Reads">
              {formatNumber(query.avg_disk_reads)}
            </Descriptions.Item>
            <Descriptions.Item label="Physical Read Requests">
              {query.physical_read_requests !== undefined
                ? formatNumber(query.physical_read_requests)
                : 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="Physical Read Bytes">
              {query.physical_read_bytes !== undefined
                ? formatBytes(query.physical_read_bytes)
                : 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="Physical Write Requests">
              {query.physical_write_requests !== undefined
                ? formatNumber(query.physical_write_requests)
                : 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="Physical Write Bytes">
              {query.physical_write_bytes !== undefined
                ? formatBytes(query.physical_write_bytes)
                : 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="Sorts">
              {query.sorts !== undefined ? formatNumber(query.sorts) : 'N/A'}
            </Descriptions.Item>
          </Descriptions>
        </Card>

        {/* Wait Events */}
        {(query.application_wait_time ||
          query.concurrency_wait_time ||
          query.cluster_wait_time ||
          query.user_io_wait_time) && (
          <Card title="Wait Events">
            <Descriptions bordered size="small" column={{ xs: 1, sm: 2, md: 3 }}>
              <Descriptions.Item label="Application Wait">
                {query.application_wait_time !== undefined
                  ? formatElapsedTime(query.application_wait_time)
                  : 'N/A'}
              </Descriptions.Item>
              <Descriptions.Item label="Concurrency Wait">
                {query.concurrency_wait_time !== undefined
                  ? formatElapsedTime(query.concurrency_wait_time)
                  : 'N/A'}
              </Descriptions.Item>
              <Descriptions.Item label="Cluster Wait">
                {query.cluster_wait_time !== undefined
                  ? formatElapsedTime(query.cluster_wait_time)
                  : 'N/A'}
              </Descriptions.Item>
              <Descriptions.Item label="User I/O Wait">
                {query.user_io_wait_time !== undefined
                  ? formatElapsedTime(query.user_io_wait_time)
                  : 'N/A'}
              </Descriptions.Item>
            </Descriptions>
          </Card>
        )}

        {/* Optimizer and Plan Info */}
        <Card title="Optimizer and Execution Plan">
          <Descriptions bordered size="small" column={{ xs: 1, sm: 2, md: 3 }}>
            <Descriptions.Item label="Plan Hash Value">
              {query.plan_hash_value !== undefined ? (
                <Text code>{query.plan_hash_value}</Text>
              ) : (
                'N/A'
              )}
            </Descriptions.Item>
            <Descriptions.Item label="Optimizer Mode">
              {query.optimizer_mode || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="Optimizer Cost">
              {query.optimizer_cost !== undefined ? formatNumber(query.optimizer_cost) : 'N/A'}
            </Descriptions.Item>
          </Descriptions>
        </Card>

        {/* Memory Usage */}
        {(query.sharable_mem || query.persistent_mem || query.runtime_mem) && (
          <Card title="Memory Usage">
            <Descriptions bordered size="small" column={{ xs: 1, sm: 2, md: 3 }}>
              <Descriptions.Item label="Sharable Memory">
                {query.sharable_mem !== undefined ? formatBytes(query.sharable_mem) : 'N/A'}
              </Descriptions.Item>
              <Descriptions.Item label="Persistent Memory">
                {query.persistent_mem !== undefined ? formatBytes(query.persistent_mem) : 'N/A'}
              </Descriptions.Item>
              <Descriptions.Item label="Runtime Memory">
                {query.runtime_mem !== undefined ? formatBytes(query.runtime_mem) : 'N/A'}
              </Descriptions.Item>
            </Descriptions>
          </Card>
        )}

        {/* Additional Statistics */}
        {data.statistics && (
          <Card title="Statistics Summary">
            <Descriptions bordered size="small" column={{ xs: 1, sm: 2, md: 3 }}>
              <Descriptions.Item label="Total Queries in Database">
                {formatNumber(data.statistics.total_queries)}
              </Descriptions.Item>
              <Descriptions.Item label="Total Executions">
                {formatNumber(data.statistics.total_executions)}
              </Descriptions.Item>
              <Descriptions.Item label="Average Elapsed Time">
                {formatElapsedTime(data.statistics.avg_elapsed_time)}
              </Descriptions.Item>
            </Descriptions>
          </Card>
        )}
      </Space>
    </div>
  );
};

export default QueryDetails;
