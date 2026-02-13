/**
 * Recommendations panel component.
 */

import React from 'react';
import { List, Tag, Card, Collapse } from 'antd';
import { ComparisonRecommendation } from '../../types/planComparison';
import { getPriorityColor, getRecommendationTypeIcon } from '../../api/planComparison';

interface RecommendationsPanelProps {
  recommendations: ComparisonRecommendation[];
}

const RecommendationsPanel: React.FC<RecommendationsPanelProps> = ({ recommendations }) => {
  return (
    <List
      dataSource={recommendations}
      renderItem={(rec) => (
        <Card size="small" style={{ marginBottom: 8 }}>
          <List.Item>
            <List.Item.Meta
              avatar={<span style={{ fontSize: 24 }}>{getRecommendationTypeIcon(rec.type)}</span>}
              title={
                <span>
                  <Tag color={getPriorityColor(rec.priority)}>{rec.priority.toUpperCase()}</Tag>
                  {rec.message}
                </span>
              }
              description={
                <div style={{ marginTop: 8 }}>
                  {rec.actions && rec.actions.length > 0 && (
                    <div>
                      <strong>Suggested Actions:</strong>
                      <ul style={{ marginTop: 8, paddingLeft: 20 }}>
                        {rec.actions.map((action, idx) => (
                          <li key={idx}>{action}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {rec.details && rec.details.length > 0 && (
                    <div style={{ marginTop: 8 }}>
                      <strong>Details:</strong>
                      <ul style={{ marginTop: 4, paddingLeft: 20 }}>
                        {rec.details.map((detail, idx) => (
                          <li key={idx}>{detail}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              }
            />
          </List.Item>
        </Card>
      )}
    />
  );
};

export default RecommendationsPanel;
