/**
 * Comparison metrics chart component.
 */

import React from 'react';
import { Card, Row, Col } from 'antd';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import { toRegressionChartData } from '../../api/planComparison';

interface ComparisonMetricsChartProps {
  currentMetrics: Record<string, any>;
  historicalMetrics: Record<string, any>;
}

const ComparisonMetricsChart: React.FC<ComparisonMetricsChartProps> = ({
  currentMetrics,
  historicalMetrics,
}) => {
  const chartData = toRegressionChartData(currentMetrics, historicalMetrics);

  if (chartData.length === 0) {
    return null;
  }

  return (
    <Card title="Metrics Comparison" size="small">
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="metric" />
          <YAxis />
          <Tooltip
            formatter={(value: any) => value.toLocaleString()}
            labelStyle={{ color: '#000' }}
          />
          <Legend />
          <Bar dataKey="historical" fill="#52c41a" name="Historical" />
          <Bar dataKey="current" fill="#1890ff" name="Current">
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.is_regression ? '#ff4d4f' : '#1890ff'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <Row gutter={16} style={{ marginTop: 16 }}>
        {chartData.map((data, idx) => (
          <Col span={6} key={idx}>
            <Card size="small">
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 12, color: '#999' }}>{data.metric}</div>
                <div
                  style={{
                    fontSize: 18,
                    fontWeight: 'bold',
                    color: data.is_regression ? '#ff4d4f' : data.change_percent < -20 ? '#52c41a' : '#000',
                  }}
                >
                  {data.change_percent >= 0 ? '+' : ''}
                  {data.change_percent.toFixed(1)}%
                </div>
              </div>
            </Card>
          </Col>
        ))}
      </Row>
    </Card>
  );
};

export default ComparisonMetricsChart;
