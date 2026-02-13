/**
 * ExecutionPlanTree component - visualizes execution plans as interactive tree.
 */

import React, { useState, useMemo } from 'react';
import {
  Tree,
  Card,
  Space,
  Tag,
  Typography,
  Tooltip,
  Row,
  Col,
  Statistic,
  Alert,
  Button,
  Drawer,
} from 'antd';
import type { DataNode } from 'antd/es/tree';
import {
  WarningOutlined,
  ThunderboltOutlined,
  DownloadOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import { PlanNode, PlanOperation, ExecutionPlan } from '../../types/executionPlan';
import {
  getOperationDisplayName,
  getSeverityColor,
  formatCost,
  formatCardinality,
  isCostlyOperation,
  getOperationIcon,
} from '../../api/executionPlans';
import PlanOperationDetail from './PlanOperationDetail';

const { Text, Title } = Typography;

interface ExecutionPlanTreeProps {
  plan: ExecutionPlan;
  onExport?: (format: 'text' | 'json' | 'xml') => void;
}

const ExecutionPlanTree: React.FC<ExecutionPlanTreeProps> = ({ plan, onExport }) => {
  const [selectedOperation, setSelectedOperation] = useState<PlanOperation | null>(null);
  const [expandedKeys, setExpandedKeys] = useState<React.Key[]>([]);
  const [drawerVisible, setDrawerVisible] = useState(false);

  // Convert PlanNode to Ant Design TreeNode format
  const convertToTreeNode = (node: PlanNode): DataNode => {
    const operationName = getOperationDisplayName(node.operation, node.options);
    const icon = getOperationIcon(node.operation);
    const costly = isCostlyOperation(node.cost);

    const title = (
      <Space size="small" wrap style={{ width: '100%' }}>
        <Text>{icon}</Text>
        <Text strong style={{ color: costly ? '#cf1322' : 'inherit' }}>
          {operationName}
        </Text>
        {node.object_name && (
          <Tag color="blue" style={{ margin: 0 }}>
            {node.object_name}
          </Tag>
        )}
        {node.cost !== undefined && (
          <Tag color={costly ? 'red' : 'default'} style={{ margin: 0 }}>
            Cost: {formatCost(node.cost)}
          </Tag>
        )}
        {node.cardinality !== undefined && (
          <Tag color="green" style={{ margin: 0 }}>
            Rows: {formatCardinality(node.cardinality)}
          </Tag>
        )}
        {costly && (
          <Tooltip title="High cost operation">
            <WarningOutlined style={{ color: '#cf1322' }} />
          </Tooltip>
        )}
      </Space>
    );

    return {
      key: `${node.id}`,
      title,
      children: node.children?.map(convertToTreeNode) || [],
      // Store the original operation data
      data: node,
    };
  };

  // Build tree data
  const treeData = useMemo(() => {
    if (!plan.plan_tree || !plan.plan_tree.id) {
      return [];
    }
    return [convertToTreeNode(plan.plan_tree)];
  }, [plan.plan_tree]);

  // Auto-expand first level
  React.useEffect(() => {
    if (treeData.length > 0) {
      const keys: React.Key[] = ['0'];
      setExpandedKeys(keys);
    }
  }, [treeData]);

  // Handle node selection
  const handleSelect = (selectedKeys: React.Key[], info: any) => {
    if (selectedKeys.length > 0 && info.node.data) {
      setSelectedOperation(info.node.data);
      setDrawerVisible(true);
    }
  };

  // Handle expand/collapse
  const handleExpand = (expandedKeys: React.Key[]) => {
    setExpandedKeys(expandedKeys);
  };

  // Expand all nodes
  const handleExpandAll = () => {
    const getAllKeys = (nodes: DataNode[]): React.Key[] => {
      let keys: React.Key[] = [];
      nodes.forEach((node) => {
        keys.push(node.key);
        if (node.children) {
          keys = keys.concat(getAllKeys(node.children));
        }
      });
      return keys;
    };
    setExpandedKeys(getAllKeys(treeData));
  };

  // Collapse all nodes
  const handleCollapseAll = () => {
    setExpandedKeys([]);
  };

  return (
    <div>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* Plan Overview */}
        <Card>
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12} md={6}>
              <Statistic
                title="Total Cost"
                value={plan.analysis.metrics.total_cost}
                formatter={(value) => formatCost(value as number)}
                prefix={<ThunderboltOutlined />}
              />
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Statistic
                title="Total Rows"
                value={plan.analysis.metrics.total_cardinality}
                formatter={(value) => formatCardinality(value as number)}
              />
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Statistic
                title="Operations"
                value={plan.analysis.metrics.operation_count}
              />
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Statistic title="Max Depth" value={plan.analysis.metrics.max_depth} />
            </Col>
          </Row>

          {/* Export Buttons */}
          <Row style={{ marginTop: 16 }}>
            <Col>
              <Space>
                <Button
                  icon={<DownloadOutlined />}
                  onClick={() => onExport?.('text')}
                  size="small"
                >
                  Export Text
                </Button>
                <Button
                  icon={<DownloadOutlined />}
                  onClick={() => onExport?.('json')}
                  size="small"
                >
                  Export JSON
                </Button>
                <Button
                  icon={<DownloadOutlined />}
                  onClick={() => onExport?.('xml')}
                  size="small"
                >
                  Export XML
                </Button>
              </Space>
            </Col>
          </Row>
        </Card>

        {/* Issues and Warnings */}
        {plan.analysis.issues.length > 0 && (
          <Card title={<><WarningOutlined /> Issues Detected</>}>
            <Space direction="vertical" style={{ width: '100%' }}>
              {plan.analysis.issues.map((issue, index) => (
                <Alert
                  key={index}
                  message={issue.message}
                  type={
                    issue.severity === 'high'
                      ? 'error'
                      : issue.severity === 'medium'
                      ? 'warning'
                      : 'info'
                  }
                  showIcon
                  description={
                    issue.operations && issue.operations.length > 0 ? (
                      <Text type="secondary">
                        Affects {issue.operations.length} operation(s)
                      </Text>
                    ) : undefined
                  }
                />
              ))}
            </Space>
          </Card>
        )}

        {/* Execution Plan Tree */}
        <Card
          title={
            <Space>
              <Text strong>Execution Plan</Text>
              <Tag color="blue">{plan.sql_id}</Tag>
              {plan.plan_hash_value && (
                <Tag color="purple">PHV: {plan.plan_hash_value}</Tag>
              )}
            </Space>
          }
          extra={
            <Space>
              <Button size="small" onClick={handleExpandAll}>
                Expand All
              </Button>
              <Button size="small" onClick={handleCollapseAll}>
                Collapse All
              </Button>
              <Tooltip title="Click on any operation to see details">
                <InfoCircleOutlined />
              </Tooltip>
            </Space>
          }
        >
          {treeData.length > 0 ? (
            <Tree
              showLine={{ showLeafIcon: false }}
              expandedKeys={expandedKeys}
              onExpand={handleExpand}
              onSelect={handleSelect}
              treeData={treeData}
              style={{
                backgroundColor: '#fafafa',
                padding: '16px',
                borderRadius: '4px',
              }}
            />
          ) : (
            <Alert
              message="No Execution Plan"
              description="No execution plan data available for this query."
              type="info"
              showIcon
            />
          )}
        </Card>

        {/* Costly Operations */}
        {plan.analysis.costly_operations.length > 0 && (
          <Card title="Top 5 Costly Operations">
            <Space direction="vertical" style={{ width: '100%' }}>
              {plan.analysis.costly_operations.map((op, index) => (
                <Card key={op.id} size="small" style={{ backgroundColor: '#fff1f0' }}>
                  <Row justify="space-between" align="middle">
                    <Col>
                      <Space>
                        <Tag color="red">#{index + 1}</Tag>
                        <Text strong>
                          {getOperationDisplayName(op.operation, op.options)}
                        </Text>
                        {op.object_name && <Tag color="blue">{op.object_name}</Tag>}
                      </Space>
                    </Col>
                    <Col>
                      <Space>
                        <Statistic
                          title="Cost"
                          value={op.cost}
                          valueStyle={{ fontSize: '16px' }}
                        />
                        <Statistic
                          title="Rows"
                          value={formatCardinality(op.cardinality)}
                          valueStyle={{ fontSize: '16px' }}
                        />
                      </Space>
                    </Col>
                  </Row>
                </Card>
              ))}
            </Space>
          </Card>
        )}
      </Space>

      {/* Operation Detail Drawer */}
      <Drawer
        title="Operation Details"
        placement="right"
        width={600}
        open={drawerVisible}
        onClose={() => setDrawerVisible(false)}
      >
        {selectedOperation && <PlanOperationDetail operation={selectedOperation} />}
      </Drawer>
    </div>
  );
};

export default ExecutionPlanTree;
