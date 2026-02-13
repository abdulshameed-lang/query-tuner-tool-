/**
 * Individual recommendation card component.
 */

import React from 'react';
import { Card, Tag, Button, Space, Collapse, message } from 'antd';
import { CopyOutlined, ThunderboltOutlined } from '@ant-design/icons';
import { Recommendation } from '../../types/recommendation';
import {
  getPriorityColor,
  getImpactColor,
  getPriorityIcon,
  getTypeIcon,
  formatRecommendationType,
  copySQLToClipboard,
} from '../../api/recommendations';

interface RecommendationCardProps {
  recommendation: Recommendation;
}

const RecommendationCard: React.FC<RecommendationCardProps> = ({ recommendation }) => {
  const handleCopySQL = async () => {
    const sql = (recommendation as any).sql || (recommendation as any).hint;
    const success = await copySQLToClipboard(sql);
    if (success) {
      message.success('SQL copied to clipboard');
    } else {
      message.error('Failed to copy SQL');
    }
  };

  const hasSQLOrHint = (recommendation as any).sql || (recommendation as any).hint;

  return (
    <Card
      size="small"
      style={{ marginBottom: 12 }}
      styles={{
        body: { padding: '16px' },
      }}
    >
      {/* Header */}
      <div style={{ marginBottom: 12 }}>
        <Space>
          <span style={{ fontSize: 24 }}>{getTypeIcon(recommendation.type)}</span>
          <Tag color={getPriorityColor(recommendation.priority)}>
            {getPriorityIcon(recommendation.priority)} {recommendation.priority.toUpperCase()}
          </Tag>
          <Tag color={getImpactColor(recommendation.estimated_impact)}>
            <ThunderboltOutlined /> {recommendation.estimated_impact.toUpperCase()} IMPACT
          </Tag>
          <Tag>{formatRecommendationType(recommendation.type)}</Tag>
        </Space>
        {hasSQLOrHint && (
          <Button
            icon={<CopyOutlined />}
            onClick={handleCopySQL}
            size="small"
            style={{ float: 'right' }}
          >
            Copy SQL
          </Button>
        )}
      </div>

      {/* Title */}
      <h3 style={{ marginTop: 0, marginBottom: 8 }}>{recommendation.title}</h3>

      {/* Description */}
      <p style={{ color: '#666', marginBottom: 12 }}>{recommendation.description}</p>

      {/* Additional Details */}
      <Collapse ghost>
        {/* Rationale */}
        {recommendation.rationale && recommendation.rationale.length > 0 && (
          <Collapse.Panel header="Rationale" key="rationale">
            <ul style={{ marginBottom: 0, paddingLeft: 20 }}>
              {recommendation.rationale.map((item, idx) => (
                <li key={idx}>{item}</li>
              ))}
            </ul>
          </Collapse.Panel>
        )}

        {/* Implementation Notes */}
        {recommendation.implementation_notes && recommendation.implementation_notes.length > 0 && (
          <Collapse.Panel header="Implementation Notes" key="notes">
            <ul style={{ marginBottom: 0, paddingLeft: 20 }}>
              {recommendation.implementation_notes.map((note, idx) => (
                <li key={idx}>{note}</li>
              ))}
            </ul>
          </Collapse.Panel>
        )}

        {/* SQL Code (for index and statistics recommendations) */}
        {(recommendation as any).sql && (
          <Collapse.Panel header="SQL Code" key="sql">
            <pre
              style={{
                backgroundColor: '#f5f5f5',
                padding: 12,
                borderRadius: 4,
                overflow: 'auto',
                maxHeight: 300,
              }}
            >
              {(recommendation as any).sql}
            </pre>
          </Collapse.Panel>
        )}

        {/* Hint (for optimizer hint recommendations) */}
        {(recommendation as any).hint && (
          <Collapse.Panel header="Optimizer Hint" key="hint">
            <pre
              style={{
                backgroundColor: '#f5f5f5',
                padding: 12,
                borderRadius: 4,
              }}
            >
              {(recommendation as any).hint}
            </pre>
          </Collapse.Panel>
        )}

        {/* SQL Patterns (for rewrite recommendations) */}
        {(recommendation as any).original_pattern && (
          <Collapse.Panel header="SQL Patterns" key="patterns">
            <div>
              <strong>Current Pattern:</strong>
              <pre
                style={{
                  backgroundColor: '#fff7e6',
                  padding: 8,
                  borderRadius: 4,
                  marginTop: 4,
                  marginBottom: 12,
                }}
              >
                {(recommendation as any).original_pattern}
              </pre>

              <strong>Suggested Pattern:</strong>
              <pre
                style={{
                  backgroundColor: '#f6ffed',
                  padding: 8,
                  borderRadius: 4,
                  marginTop: 4,
                }}
              >
                {(recommendation as any).suggested_pattern}
              </pre>
            </div>
          </Collapse.Panel>
        )}

        {/* Table/Index Details */}
        {((recommendation as any).table || (recommendation as any).columns) && (
          <Collapse.Panel header="Details" key="details">
            {(recommendation as any).table && (
              <div>
                <strong>Table:</strong> {(recommendation as any).table}
              </div>
            )}
            {(recommendation as any).columns && (
              <div>
                <strong>Columns:</strong> {(recommendation as any).columns.join(', ')}
              </div>
            )}
            {(recommendation as any).cost !== undefined && (
              <div>
                <strong>Current Cost:</strong> {(recommendation as any).cost.toLocaleString()}
              </div>
            )}
            {(recommendation as any).cardinality !== undefined && (
              <div>
                <strong>Cardinality:</strong> {(recommendation as any).cardinality.toLocaleString()}
              </div>
            )}
          </Collapse.Panel>
        )}
      </Collapse>
    </Card>
  );
};

export default RecommendationCard;
