/**
 * Baseline recommendation panel component.
 */

import React, { useState } from 'react';
import { Card, Button, Alert, Spin, message, Descriptions, Tag } from 'antd';
import { CopyOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { useBaselineRecommendation } from '../../api/planComparison';
import { getPriorityColor, copyBaselineSQLToClipboard } from '../../api/planComparison';

interface BaselineRecommendationPanelProps {
  sqlId: string;
  currentPlanHash?: number;
  preferredPlanHash?: number;
}

const BaselineRecommendationPanel: React.FC<BaselineRecommendationPanelProps> = ({
  sqlId,
  currentPlanHash,
  preferredPlanHash,
}) => {
  const [recommendation, setRecommendation] = useState<any>(null);
  const { mutate, isLoading } = useBaselineRecommendation();

  React.useEffect(() => {
    if (currentPlanHash && preferredPlanHash) {
      mutate(
        { sql_id: sqlId, current_plan_hash: currentPlanHash, preferred_plan_hash: preferredPlanHash },
        {
          onSuccess: (data) => setRecommendation(data),
          onError: () => message.error('Failed to generate baseline recommendation'),
        }
      );
    }
  }, [sqlId, currentPlanHash, preferredPlanHash, mutate]);

  const handleCopySQL = async () => {
    const success = await copyBaselineSQLToClipboard(recommendation?.baseline_creation_sql);
    if (success) {
      message.success('SQL copied to clipboard');
    } else {
      message.error('Failed to copy SQL');
    }
  };

  if (isLoading) {
    return <Spin tip="Generating baseline recommendation..." />;
  }

  if (!recommendation) {
    return <Alert message="No recommendation data available" type="info" />;
  }

  if (!recommendation.recommend_baseline) {
    return (
      <Alert
        message="SQL Plan Baseline Not Recommended"
        description={recommendation.reasons?.join('. ') || 'No significant issues detected.'}
        type="success"
        showIcon
        icon={<CheckCircleOutlined />}
      />
    );
  }

  return (
    <div>
      <Alert
        message={`${recommendation.priority.toUpperCase()} Priority: SQL Plan Baseline Recommended`}
        description={recommendation.reasons?.join('. ')}
        type="warning"
        showIcon
        style={{ marginBottom: 16 }}
      />

      <Card size="small" title="Baseline Details" style={{ marginBottom: 16 }}>
        <Descriptions bordered column={1}>
          <Descriptions.Item label="SQL ID">{recommendation.sql_id}</Descriptions.Item>
          <Descriptions.Item label="Preferred Plan Hash">
            {recommendation.preferred_plan_hash}
          </Descriptions.Item>
          <Descriptions.Item label="Priority">
            <Tag color={getPriorityColor(recommendation.priority)}>
              {recommendation.priority.toUpperCase()}
            </Tag>
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {recommendation.instructions && (
        <Card size="small" title="Implementation Instructions" style={{ marginBottom: 16 }}>
          <ol>
            {recommendation.instructions.map((instruction: string, idx: number) => (
              <li key={idx} style={{ marginBottom: 8 }}>
                {instruction}
              </li>
            ))}
          </ol>
        </Card>
      )}

      {recommendation.baseline_creation_sql && (
        <Card
          size="small"
          title="Baseline Creation SQL"
          extra={
            <Button
              icon={<CopyOutlined />}
              onClick={handleCopySQL}
              size="small"
            >
              Copy SQL
            </Button>
          }
        >
          <pre
            style={{
              backgroundColor: '#f5f5f5',
              padding: 12,
              borderRadius: 4,
              overflow: 'auto',
              maxHeight: 400,
            }}
          >
            {recommendation.baseline_creation_sql}
          </pre>
        </Card>
      )}
    </div>
  );
};

export default BaselineRecommendationPanel;
