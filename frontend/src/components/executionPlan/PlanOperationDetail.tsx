/**
 * PlanOperationDetail component - displays detailed information for a plan operation.
 */

import React from 'react';
import {
  Descriptions,
  Card,
  Space,
  Tag,
  Typography,
  Alert,
  Divider,
  Row,
  Col,
  Statistic,
} from 'antd';
import {
  ThunderboltOutlined,
  WarningOutlined,
  DatabaseOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import { PlanOperation } from '../../types/executionPlan';
import {
  getOperationDisplayName,
  formatCost,
  formatCardinality,
  isCostlyOperation,
  getOperationIcon,
} from '../../api/executionPlans';
import { formatBytes } from '../../api/queries';

const { Text, Paragraph, Title } = Typography;

interface PlanOperationDetailProps {
  operation: PlanOperation;
}

const PlanOperationDetail: React.FC<PlanOperationDetailProps> = ({ operation }) => {
  const operationName = getOperationDisplayName(operation.operation, operation.options);
  const icon = getOperationIcon(operation.operation);
  const costly = isCostlyOperation(operation.cost);

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      {/* Header */}
      <Card>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Title level={4} style={{ margin: 0 }}>
            {icon} {operationName}
          </Title>

          <Space wrap>
            <Tag color="blue">ID: {operation.id}</Tag>
            {operation.parent_id !== null && operation.parent_id !== undefined && (
              <Tag>Parent: {operation.parent_id}</Tag>
            )}
            {operation.depth !== undefined && <Tag>Depth: {operation.depth}</Tag>}
            {costly && (
              <Tag color="red" icon={<WarningOutlined />}>
                HIGH COST
              </Tag>
            )}
          </Space>
        </Space>
      </Card>

      {/* Cost Metrics */}
      <Card title={<><ThunderboltOutlined /> Cost Metrics</>}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={8}>
            <Statistic
              title="Cost"
              value={operation.cost}
              formatter={(value) => formatCost(value as number)}
              valueStyle={{
                color: costly ? '#cf1322' : 'inherit',
              }}
            />
          </Col>
          <Col xs={24} sm={12} md={8}>
            <Statistic
              title="Cardinality"
              value={operation.cardinality}
              formatter={(value) => formatCardinality(value as number)}
            />
          </Col>
          <Col xs={24} sm={12} md={8}>
            <Statistic
              title="Bytes"
              value={operation.bytes}
              formatter={(value) =>
                value ? formatBytes(value as number) : 'N/A'
              }
            />
          </Col>
          {operation.cpu_cost !== undefined && (
            <Col xs={24} sm={12} md={8}>
              <Statistic
                title="CPU Cost"
                value={operation.cpu_cost}
                formatter={(value) => formatCost(value as number)}
              />
            </Col>
          )}
          {operation.io_cost !== undefined && (
            <Col xs={24} sm={12} md={8}>
              <Statistic
                title="I/O Cost"
                value={operation.io_cost}
                formatter={(value) => formatCost(value as number)}
              />
            </Col>
          )}
          {operation.temp_space !== undefined && operation.temp_space > 0 && (
            <Col xs={24} sm={12} md={8}>
              <Statistic
                title="Temp Space"
                value={operation.temp_space}
                formatter={(value) => formatBytes(value as number)}
              />
            </Col>
          )}
        </Row>

        {/* Cumulative metrics if available */}
        {(operation.cumulative_cost || operation.cumulative_cardinality) && (
          <>
            <Divider />
            <Row gutter={[16, 16]}>
              {operation.cumulative_cost !== undefined && (
                <Col xs={24} sm={12}>
                  <Statistic
                    title="Cumulative Cost"
                    value={operation.cumulative_cost}
                    formatter={(value) => formatCost(value as number)}
                  />
                </Col>
              )}
              {operation.cumulative_cardinality !== undefined && (
                <Col xs={24} sm={12}>
                  <Statistic
                    title="Cumulative Cardinality"
                    value={operation.cumulative_cardinality}
                    formatter={(value) => formatCardinality(value as number)}
                  />
                </Col>
              )}
            </Row>
          </>
        )}
      </Card>

      {/* Object Information */}
      {(operation.object_name || operation.object_owner || operation.object_type) && (
        <Card title={<><DatabaseOutlined /> Object Information</>}>
          <Descriptions bordered size="small" column={1}>
            {operation.object_name && (
              <Descriptions.Item label="Object Name">
                <Text code>{operation.object_name}</Text>
              </Descriptions.Item>
            )}
            {operation.object_owner && (
              <Descriptions.Item label="Owner">{operation.object_owner}</Descriptions.Item>
            )}
            {operation.object_type && (
              <Descriptions.Item label="Type">{operation.object_type}</Descriptions.Item>
            )}
            {operation.object_alias && (
              <Descriptions.Item label="Alias">{operation.object_alias}</Descriptions.Item>
            )}
          </Descriptions>
        </Card>
      )}

      {/* Predicates */}
      {(operation.access_predicates || operation.filter_predicates) && (
        <Card title={<><FileTextOutlined /> Predicates</>}>
          {operation.access_predicates && (
            <>
              <Text strong>Access Predicates:</Text>
              <Paragraph
                code
                copyable
                style={{
                  backgroundColor: '#f5f5f5',
                  padding: '12px',
                  borderRadius: '4px',
                  marginTop: '8px',
                  marginBottom: '16px',
                  whiteSpace: 'pre-wrap',
                }}
              >
                {operation.access_predicates}
              </Paragraph>
            </>
          )}
          {operation.filter_predicates && (
            <>
              <Text strong>Filter Predicates:</Text>
              <Paragraph
                code
                copyable
                style={{
                  backgroundColor: '#f5f5f5',
                  padding: '12px',
                  borderRadius: '4px',
                  marginTop: '8px',
                  whiteSpace: 'pre-wrap',
                }}
              >
                {operation.filter_predicates}
              </Paragraph>
            </>
          )}
        </Card>
      )}

      {/* Additional Details */}
      <Card title="Additional Details">
        <Descriptions bordered size="small" column={{ xs: 1, sm: 2 }}>
          {operation.optimizer && (
            <Descriptions.Item label="Optimizer">{operation.optimizer}</Descriptions.Item>
          )}
          {operation.position !== undefined && (
            <Descriptions.Item label="Position">{operation.position}</Descriptions.Item>
          )}
          {operation.search_columns !== undefined && operation.search_columns > 0 && (
            <Descriptions.Item label="Search Columns">
              {operation.search_columns}
            </Descriptions.Item>
          )}
          {operation.qblock_name && (
            <Descriptions.Item label="Query Block">{operation.qblock_name}</Descriptions.Item>
          )}
          {operation.distribution && (
            <Descriptions.Item label="Distribution">
              <Tag color="purple">{operation.distribution}</Tag>
            </Descriptions.Item>
          )}
          {operation.partition_start && (
            <Descriptions.Item label="Partition Start">
              {operation.partition_start}
            </Descriptions.Item>
          )}
          {operation.partition_stop && (
            <Descriptions.Item label="Partition Stop">
              {operation.partition_stop}
            </Descriptions.Item>
          )}
          {operation.partition_id !== undefined && (
            <Descriptions.Item label="Partition ID">
              {operation.partition_id}
            </Descriptions.Item>
          )}
          {operation.time !== undefined && operation.time > 0 && (
            <Descriptions.Item label="Time">{operation.time}</Descriptions.Item>
          )}
        </Descriptions>
      </Card>

      {/* Projection */}
      {operation.projection && (
        <Card title="Projection">
          <Paragraph
            code
            copyable
            style={{
              backgroundColor: '#f5f5f5',
              padding: '12px',
              borderRadius: '4px',
              whiteSpace: 'pre-wrap',
            }}
          >
            {operation.projection}
          </Paragraph>
        </Card>
      )}

      {/* Remarks */}
      {operation.remarks && (
        <Alert
          message="Remarks"
          description={operation.remarks}
          type="info"
          showIcon
        />
      )}

      {/* Recommendations based on operation type */}
      {operation.operation === 'TABLE ACCESS' && operation.options === 'FULL' && (
        <Alert
          message="Full Table Scan Detected"
          description="This operation performs a full table scan which can be inefficient for large tables. Consider adding an index on the columns used in the WHERE clause."
          type="warning"
          showIcon
          icon={<WarningOutlined />}
        />
      )}

      {operation.operation.includes('CARTESIAN') && (
        <Alert
          message="Cartesian Product Detected"
          description="This operation produces a Cartesian product which typically indicates a missing join condition. Review the query for proper join conditions."
          type="error"
          showIcon
          icon={<WarningOutlined />}
        />
      )}
    </Space>
  );
};

export default PlanOperationDetail;
