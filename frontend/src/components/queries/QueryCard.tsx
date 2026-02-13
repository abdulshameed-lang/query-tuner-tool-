/**
 * QueryCard component - displays a query summary in a card format.
 */

import React from 'react';
import { Card, Descriptions, Tag, Typography, Space } from 'antd';
import { ClockCircleOutlined, ThunderboltOutlined } from '@ant-design/icons';
import { Query } from '../../types/query';
import { formatElapsedTime, formatNumber } from '../../api/queries';

const { Text, Paragraph } = Typography;

interface QueryCardProps {
  query: Query;
  onClick?: () => void;
}

const QueryCard: React.FC<QueryCardProps> = ({ query, onClick }) => {
  return (
    <Card
      hoverable={!!onClick}
      onClick={onClick}
      style={{ marginBottom: 16 }}
      title={
        <Space>
          <Text code copyable={{ text: query.sql_id }}>
            {query.sql_id}
          </Text>
          {query.needs_tuning && (
            <Tag color="red" icon={<ThunderboltOutlined />}>
              NEEDS TUNING
            </Tag>
          )}
        </Space>
      }
      extra={
        <Space>
          <Text type="secondary">Schema:</Text>
          <Text strong>{query.parsing_schema_name}</Text>
        </Space>
      }
    >
      {/* SQL Text */}
      <Paragraph
        ellipsis={{ rows: 3, expandable: true, symbol: 'more' }}
        style={{
          backgroundColor: '#f5f5f5',
          padding: '12px',
          borderRadius: '4px',
          fontFamily: 'monospace',
          fontSize: '13px',
          marginBottom: 16,
        }}
      >
        {query.sql_text}
      </Paragraph>

      {/* Performance Metrics */}
      <Descriptions size="small" column={{ xs: 1, sm: 2, md: 3 }}>
        <Descriptions.Item
          label={
            <Space>
              <ClockCircleOutlined />
              Elapsed Time
            </Space>
          }
        >
          <Text strong>{formatElapsedTime(query.elapsed_time)}</Text>
        </Descriptions.Item>
        <Descriptions.Item label="Avg Elapsed">
          <Text>{formatElapsedTime(query.avg_elapsed_time)}</Text>
        </Descriptions.Item>
        <Descriptions.Item label="Executions">
          <Text>{formatNumber(query.executions)}</Text>
        </Descriptions.Item>
        <Descriptions.Item label="CPU Time">
          <Text>{formatElapsedTime(query.cpu_time)}</Text>
        </Descriptions.Item>
        <Descriptions.Item label="Buffer Gets">
          <Text>{formatNumber(query.buffer_gets)}</Text>
        </Descriptions.Item>
        <Descriptions.Item label="Disk Reads">
          <Text>{formatNumber(query.disk_reads)}</Text>
        </Descriptions.Item>
        <Descriptions.Item label="Rows Processed">
          <Text>{formatNumber(query.rows_processed)}</Text>
        </Descriptions.Item>
        <Descriptions.Item label="Impact Score">
          <Tag color={query.impact_score > 50 ? 'red' : query.impact_score > 25 ? 'orange' : 'green'}>
            {query.impact_score.toFixed(2)}
          </Tag>
        </Descriptions.Item>
      </Descriptions>
    </Card>
  );
};

export default QueryCard;
