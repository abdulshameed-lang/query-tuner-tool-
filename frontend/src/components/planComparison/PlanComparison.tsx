/**
 * Main plan comparison component.
 * Displays comparison between current and historical execution plans.
 */

import React, { useState } from 'react';
import {
  Card,
  Row,
  Col,
  Spin,
  Alert,
  Tabs,
  Button,
  Space,
  Tag,
  Divider,
  Empty,
  Statistic,
} from 'antd';
import {
  SwapOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  InfoCircleOutlined,
  DownloadOutlined,
  CopyOutlined,
} from '@ant-design/icons';
import { usePlanComparison } from '../../api/planComparison';
import RegressionAnalysisPanel from './RegressionAnalysisPanel';
import PlanDiffPanel from './PlanDiffPanel';
import OperationChangesPanel from './OperationChangesPanel';
import RecommendationsPanel from './RecommendationsPanel';
import BaselineRecommendationPanel from './BaselineRecommendationPanel';
import ComparisonMetricsChart from './ComparisonMetricsChart';
import {
  getSeverityColor,
  getSeverityIcon,
  formatComparisonTimestamp,
  exportComparisonAsJSON,
  shouldRecommendBaseline,
} from '../../api/planComparison';

interface PlanComparisonProps {
  sqlId: string;
  currentPlanHash?: number;
  historicalPlanHash?: number;
  onClose?: () => void;
}

const PlanComparison: React.FC<PlanComparisonProps> = ({
  sqlId,
  currentPlanHash,
  historicalPlanHash,
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState('overview');

  const { data, isLoading, error, refetch } = usePlanComparison(
    sqlId,
    currentPlanHash,
    historicalPlanHash
  );

  const handleExport = () => {
    if (data) {
      const json = exportComparisonAsJSON(data);
      const blob = new Blob([json], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `plan-comparison-${sqlId}-${Date.now()}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
  };

  if (isLoading) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: '60px 20px' }}>
          <Spin size="large" tip="Comparing execution plans..." />
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <Alert
          message="Comparison Failed"
          description={error.message || 'Failed to compare execution plans'}
          type="error"
          showIcon
          action={
            <Button size="small" onClick={() => refetch()}>
              Retry
            </Button>
          }
        />
      </Card>
    );
  }

  if (!data?.data) {
    return (
      <Card>
        <Empty description="No comparison data available" />
      </Card>
    );
  }

  const comparison = data.data;

  if (!comparison.comparison_possible) {
    return (
      <Card>
        <Alert
          message="Comparison Not Possible"
          description={comparison.reason || 'Unable to compare plans'}
          type="warning"
          showIcon
        />
      </Card>
    );
  }

  const regressionAnalysis = comparison.regression_analysis;
  const severity = regressionAnalysis?.severity || 'none';
  const hasRegression = regressionAnalysis?.has_regression || false;
  const regressionCount = regressionAnalysis?.regression_count || 0;
  const improvementCount = regressionAnalysis?.improvement_count || 0;

  const recommendBaseline = shouldRecommendBaseline(
    regressionCount,
    severity,
    comparison.plan_diff?.total_changes || 0
  );

  return (
    <div className="plan-comparison">
      {/* Header */}
      <Card
        title={
          <Space>
            <SwapOutlined />
            <span>Execution Plan Comparison</span>
            {comparison.plans_identical && <Tag color="green">Identical Plans</Tag>}
            {hasRegression && (
              <Tag color={getSeverityColor(severity)} icon={<WarningOutlined />}>
                {getSeverityIcon(severity)} {severity.toUpperCase()} Regression
              </Tag>
            )}
          </Space>
        }
        extra={
          <Space>
            <Button
              icon={<DownloadOutlined />}
              onClick={handleExport}
              size="small"
            >
              Export
            </Button>
            {onClose && (
              <Button onClick={onClose} size="small">
                Close
              </Button>
            )}
          </Space>
        }
      >
        {/* Summary Statistics */}
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="Current Plan Hash"
                value={comparison.current_plan_hash || 'N/A'}
                valueStyle={{ fontSize: 18 }}
              />
              <div style={{ fontSize: 12, color: '#999', marginTop: 8 }}>
                {comparison.current_metadata?.first_seen &&
                  `First seen: ${new Date(
                    comparison.current_metadata.first_seen
                  ).toLocaleDateString()}`}
              </div>
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="Historical Plan Hash"
                value={comparison.historical_plan_hash || 'N/A'}
                valueStyle={{ fontSize: 18 }}
              />
              <div style={{ fontSize: 12, color: '#999', marginTop: 8 }}>
                {comparison.historical_metadata?.first_seen &&
                  `First seen: ${new Date(
                    comparison.historical_metadata.first_seen
                  ).toLocaleDateString()}`}
              </div>
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="Regressions"
                value={regressionCount}
                valueStyle={{ color: regressionCount > 0 ? '#cf1322' : '#3f8600' }}
                prefix={regressionCount > 0 ? <WarningOutlined /> : <CheckCircleOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="Improvements"
                value={improvementCount}
                valueStyle={{ color: '#3f8600' }}
                prefix={<CheckCircleOutlined />}
              />
            </Card>
          </Col>
        </Row>

        {/* Quick Actions */}
        {recommendBaseline && (
          <Alert
            message="SQL Plan Baseline Recommended"
            description="Significant performance regression detected. Consider creating a SQL Plan Baseline to stabilize plan execution."
            type="warning"
            showIcon
            icon={<InfoCircleOutlined />}
            action={
              <Button size="small" type="primary" onClick={() => setActiveTab('baseline')}>
                View Recommendation
              </Button>
            }
            style={{ marginBottom: 24 }}
          />
        )}

        {/* Comparison Timestamp */}
        <div style={{ textAlign: 'right', color: '#999', fontSize: 12, marginBottom: 16 }}>
          Comparison performed: {formatComparisonTimestamp(comparison.comparison_timestamp)}
        </div>
      </Card>

      {/* Tabs for detailed views */}
      <Card style={{ marginTop: 16 }}>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <Tabs.TabPane
            tab={
              <span>
                <InfoCircleOutlined /> Overview
              </span>
            }
            key="overview"
          >
            {/* Metrics Chart */}
            {comparison.current_metrics && comparison.historical_metrics && (
              <ComparisonMetricsChart
                currentMetrics={comparison.current_metrics}
                historicalMetrics={comparison.historical_metrics}
              />
            )}

            <Divider />

            {/* Quick Summary */}
            <Row gutter={16}>
              <Col span={12}>
                <Card size="small" title="Current Plan Summary">
                  <p>
                    <strong>Total Cost:</strong>{' '}
                    {comparison.current_metrics?.total_cost?.toLocaleString() || 'N/A'}
                  </p>
                  <p>
                    <strong>Cardinality:</strong>{' '}
                    {comparison.current_metrics?.total_cardinality?.toLocaleString() || 'N/A'}
                  </p>
                  <p>
                    <strong>Operation Count:</strong>{' '}
                    {comparison.current_metrics?.operation_count || 'N/A'}
                  </p>
                  <p>
                    <strong>Max Depth:</strong> {comparison.current_metrics?.max_depth || 'N/A'}
                  </p>
                </Card>
              </Col>
              <Col span={12}>
                <Card size="small" title="Historical Plan Summary">
                  <p>
                    <strong>Total Cost:</strong>{' '}
                    {comparison.historical_metrics?.total_cost?.toLocaleString() || 'N/A'}
                  </p>
                  <p>
                    <strong>Cardinality:</strong>{' '}
                    {comparison.historical_metrics?.total_cardinality?.toLocaleString() || 'N/A'}
                  </p>
                  <p>
                    <strong>Operation Count:</strong>{' '}
                    {comparison.historical_metrics?.operation_count || 'N/A'}
                  </p>
                  <p>
                    <strong>Max Depth:</strong> {comparison.historical_metrics?.max_depth || 'N/A'}
                  </p>
                </Card>
              </Col>
            </Row>
          </Tabs.TabPane>

          {regressionAnalysis && (
            <Tabs.TabPane
              tab={
                <span>
                  <WarningOutlined />
                  Regression Analysis
                  {regressionCount > 0 && (
                    <Tag color="red" style={{ marginLeft: 8 }}>
                      {regressionCount}
                    </Tag>
                  )}
                </span>
              }
              key="regression"
            >
              <RegressionAnalysisPanel analysis={regressionAnalysis} />
            </Tabs.TabPane>
          )}

          {comparison.plan_diff && (
            <Tabs.TabPane
              tab={
                <span>
                  <SwapOutlined />
                  Plan Differences
                  {comparison.plan_diff.total_changes > 0 && (
                    <Tag color="orange" style={{ marginLeft: 8 }}>
                      {comparison.plan_diff.total_changes}
                    </Tag>
                  )}
                </span>
              }
              key="diff"
            >
              <PlanDiffPanel diff={comparison.plan_diff} />
            </Tabs.TabPane>
          )}

          {comparison.operation_changes && comparison.operation_changes.length > 0 && (
            <Tabs.TabPane
              tab={
                <span>
                  <CopyOutlined />
                  Operation Changes
                  <Tag color="blue" style={{ marginLeft: 8 }}>
                    {comparison.operation_changes.length}
                  </Tag>
                </span>
              }
              key="operations"
            >
              <OperationChangesPanel changes={comparison.operation_changes} />
            </Tabs.TabPane>
          )}

          {comparison.recommendations && comparison.recommendations.length > 0 && (
            <Tabs.TabPane
              tab={
                <span>
                  <CheckCircleOutlined />
                  Recommendations
                  <Tag color="green" style={{ marginLeft: 8 }}>
                    {comparison.recommendations.length}
                  </Tag>
                </span>
              }
              key="recommendations"
            >
              <RecommendationsPanel recommendations={comparison.recommendations} />
            </Tabs.TabPane>
          )}

          {recommendBaseline && (
            <Tabs.TabPane
              tab={
                <span>
                  <InfoCircleOutlined />
                  Baseline Recommendation
                </span>
              }
              key="baseline"
            >
              <BaselineRecommendationPanel
                sqlId={sqlId}
                currentPlanHash={comparison.current_plan_hash}
                preferredPlanHash={comparison.historical_plan_hash}
              />
            </Tabs.TabPane>
          )}
        </Tabs>
      </Card>
    </div>
  );
};

export default PlanComparison;
