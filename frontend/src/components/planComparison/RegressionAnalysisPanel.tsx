/**
 * Regression analysis panel component.
 */

import React from 'react';
import { Card, List, Tag, Row, Col, Empty, Divider } from 'antd';
import { WarningOutlined, CheckCircleOutlined, RiseOutlined, FallOutlined } from '@ant-design/icons';
import { RegressionAnalysis } from '../../types/planComparison';
import {
  getSeverityColor,
  getSeverityIcon,
  formatPercentageChange,
  formatRatio,
} from '../../api/planComparison';

interface RegressionAnalysisPanelProps {
  analysis: RegressionAnalysis;
}

const RegressionAnalysisPanel: React.FC<RegressionAnalysisPanelProps> = ({ analysis }) => {
  const { regressions, improvements, severity, has_regression } = analysis;

  return (
    <div>
      {/* Summary Header */}
      <Card size="small" style={{ marginBottom: 16, backgroundColor: has_regression ? '#fff7e6' : '#f6ffed' }}>
        <Row gutter={16}>
          <Col span={8}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 24, fontWeight: 'bold' }}>
                {getSeverityIcon(severity)} {severity.toUpperCase()}
              </div>
              <div style={{ color: '#999', marginTop: 4 }}>Overall Severity</div>
            </div>
          </Col>
          <Col span={8}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 24, fontWeight: 'bold', color: '#cf1322' }}>
                {regressions.length}
              </div>
              <div style={{ color: '#999', marginTop: 4 }}>Regressions Found</div>
            </div>
          </Col>
          <Col span={8}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 24, fontWeight: 'bold', color: '#3f8600' }}>
                {improvements.length}
              </div>
              <div style={{ color: '#999', marginTop: 4 }}>Improvements</div>
            </div>
          </Col>
        </Row>
      </Card>

      {/* Regressions List */}
      {regressions.length > 0 && (
        <>
          <Card title={<><WarningOutlined /> Regressions Detected</>} size="small" style={{ marginBottom: 16 }}>
            <List
              dataSource={regressions}
              renderItem={(finding) => (
                <List.Item>
                  <List.Item.Meta
                    title={
                      <span>
                        <Tag color={getSeverityColor(finding.severity)}>{finding.severity.toUpperCase()}</Tag>
                        {finding.message}
                      </span>
                    }
                    description={
                      <div style={{ marginTop: 8 }}>
                        <Row gutter={16}>
                          <Col span={6}>
                            <strong>Historical:</strong> {finding.historical_value?.toLocaleString() || 'N/A'}
                          </Col>
                          <Col span={6}>
                            <strong>Current:</strong> {finding.current_value?.toLocaleString() || 'N/A'}
                          </Col>
                          {finding.ratio && (
                            <Col span={6}>
                              <strong>Ratio:</strong> <Tag color="red" icon={<RiseOutlined />}>{formatRatio(finding.ratio)}</Tag>
                            </Col>
                          )}
                          {finding.change_percent && (
                            <Col span={6}>
                              <strong>Change:</strong> <Tag color="red" icon={<RiseOutlined />}>{formatPercentageChange(finding.change_percent)}</Tag>
                            </Col>
                          )}
                        </Row>
                      </div>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </>
      )}

      {/* Improvements List */}
      {improvements.length > 0 && (
        <>
          <Card title={<><CheckCircleOutlined /> Performance Improvements</>} size="small">
            <List
              dataSource={improvements}
              renderItem={(finding) => (
                <List.Item>
                  <List.Item.Meta
                    title={
                      <span>
                        <Tag color="green">IMPROVEMENT</Tag>
                        {finding.message}
                      </span>
                    }
                    description={
                      <div style={{ marginTop: 8 }}>
                        <Row gutter={16}>
                          <Col span={6}>
                            <strong>Historical:</strong> {finding.historical_value?.toLocaleString() || 'N/A'}
                          </Col>
                          <Col span={6}>
                            <strong>Current:</strong> {finding.current_value?.toLocaleString() || 'N/A'}
                          </Col>
                          {finding.ratio && (
                            <Col span={6}>
                              <strong>Ratio:</strong> <Tag color="green" icon={<FallOutlined />}>{formatRatio(finding.ratio)}</Tag>
                            </Col>
                          )}
                          {finding.change_percent && (
                            <Col span={6}>
                              <strong>Change:</strong> <Tag color="green" icon={<FallOutlined />}>{formatPercentageChange(finding.change_percent)}</Tag>
                            </Col>
                          )}
                        </Row>
                      </div>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </>
      )}

      {/* No findings */}
      {regressions.length === 0 && improvements.length === 0 && (
        <Empty description="No significant performance changes detected" />
      )}
    </div>
  );
};

export default RegressionAnalysisPanel;
