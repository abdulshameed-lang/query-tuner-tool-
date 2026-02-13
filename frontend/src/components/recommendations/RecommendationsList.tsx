/**
 * Recommendations list component.
 * Displays all recommendations with filtering and grouping.
 */

import React, { useState } from 'react';
import { Card, List, Spin, Alert, Button, Space, Tag, Segmented, Empty, Statistic, Row, Col } from 'antd';
import { DownloadOutlined, FilterOutlined, BulbOutlined } from '@ant-design/icons';
import { useRecommendations } from '../../api/recommendations';
import RecommendationCard from './RecommendationCard';
import {
  getPriorityColor,
  getTypeIcon,
  formatRecommendationType,
  exportRecommendationsAsJSON,
  sortByUrgency,
} from '../../api/recommendations';

interface RecommendationsListProps {
  sqlId: string;
  onClose?: () => void;
}

const RecommendationsList: React.FC<RecommendationsListProps> = ({ sqlId, onClose }) => {
  const [filterType, setFilterType] = useState<string>('all');
  const { data, isLoading, error, refetch } = useRecommendations(sqlId);

  const handleExport = () => {
    if (data) {
      const json = exportRecommendationsAsJSON(data);
      const blob = new Blob([json], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `recommendations-${sqlId}-${Date.now()}.json`;
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
          <Spin size="large" tip="Generating recommendations..." />
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <Alert
          message="Failed to Load Recommendations"
          description={error.message || 'Failed to generate recommendations'}
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

  if (!data) {
    return (
      <Card>
        <Empty description="No recommendations data available" />
      </Card>
    );
  }

  const { recommendations, summary } = data;

  // Filter recommendations
  const filteredRecommendations =
    filterType === 'all'
      ? recommendations
      : recommendations.filter((rec) => rec.type === filterType);

  // Sort by urgency
  const sortedRecommendations = sortByUrgency(filteredRecommendations);

  return (
    <div className="recommendations-list">
      {/* Header Card */}
      <Card
        title={
          <Space>
            <BulbOutlined />
            <span>Query Tuning Recommendations</span>
            {summary.critical_count > 0 && (
              <Tag color="red">
                {summary.critical_count} Critical
              </Tag>
            )}
            {summary.high_impact_count > 0 && (
              <Tag color="green">
                {summary.high_impact_count} High Impact
              </Tag>
            )}
          </Space>
        }
        extra={
          <Space>
            <Button icon={<DownloadOutlined />} onClick={handleExport} size="small">
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
                title="Total Recommendations"
                value={summary.total_count}
                prefix={<BulbOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="Critical Priority"
                value={summary.critical_count}
                valueStyle={{ color: '#cf1322' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="High Impact"
                value={summary.high_impact_count}
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="Filtered Results"
                value={filteredRecommendations.length}
              />
            </Card>
          </Col>
        </Row>

        {/* Filter by Type */}
        <div style={{ marginBottom: 16 }}>
          <Space>
            <FilterOutlined />
            <Segmented
              value={filterType}
              onChange={(value) => setFilterType(value as string)}
              options={[
                { label: 'All', value: 'all' },
                ...Object.keys(summary.by_type).map((type) => ({
                  label: (
                    <span>
                      {getTypeIcon(type as any)} {formatRecommendationType(type as any)} ({summary.by_type[type]})
                    </span>
                  ),
                  value: type,
                })),
              ]}
            />
          </Space>
        </div>
      </Card>

      {/* Recommendations List */}
      <Card style={{ marginTop: 16 }}>
        {sortedRecommendations.length === 0 ? (
          <Empty description="No recommendations match the selected filter" />
        ) : (
          <List
            dataSource={sortedRecommendations}
            renderItem={(recommendation, index) => (
              <RecommendationCard key={index} recommendation={recommendation} />
            )}
            pagination={
              sortedRecommendations.length > 10
                ? {
                    pageSize: 10,
                    showSizeChanger: true,
                    showTotal: (total) => `Total ${total} recommendations`,
                  }
                : false
            }
          />
        )}
      </Card>
    </div>
  );
};

export default RecommendationsList;
