/**
 * Historical comparison component showing current vs baseline performance
 */

import React from "react";
import { Card, Descriptions, Space, Tag, Alert, Table, Row, Col, Statistic } from "antd";
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  CheckCircleOutlined,
  WarningOutlined,
} from "@ant-design/icons";
import type { HistoricalComparisonResult, MetricComparison } from "../../types/awrAsh";
import { getTrendColor } from "../../api/awrAsh";

interface HistoricalComparisonProps {
  comparison: HistoricalComparisonResult;
}

export const HistoricalComparison: React.FC<HistoricalComparisonProps> = ({
  comparison,
}) => {
  const { current, historical, comparison: metrics, trend, recommendations } = comparison;

  // Metrics to display
  const metricNames = {
    elapsed_time_sec: "Elapsed Time (sec)",
    cpu_time_sec: "CPU Time (sec)",
    buffer_gets_per_exec: "Buffer Gets per Exec",
    disk_reads_per_exec: "Disk Reads per Exec",
  };

  // Convert comparison to table data
  const tableData = Object.entries(metrics || {}).map(([key, value]) => ({
    metric: metricNames[key as keyof typeof metricNames] || key,
    current: value.current,
    baseline_mean: value.baseline_mean,
    baseline_p95: value.baseline_p95,
    change: value.change,
    change_percent: value.change_percent,
    regression: value.regression,
    improvement: value.improvement,
  }));

  const columns = [
    {
      title: "Metric",
      dataIndex: "metric",
      key: "metric",
      fixed: "left" as const,
      width: 180,
    },
    {
      title: "Current",
      dataIndex: "current",
      key: "current",
      width: 120,
      render: (val: number) => val.toFixed(2),
    },
    {
      title: "Baseline Mean",
      dataIndex: "baseline_mean",
      key: "baseline_mean",
      width: 130,
      render: (val: number) => val.toFixed(2),
    },
    {
      title: "Baseline P95",
      dataIndex: "baseline_p95",
      key: "baseline_p95",
      width: 130,
      render: (val: number) => val.toFixed(2),
    },
    {
      title: "Change",
      dataIndex: "change",
      key: "change",
      width: 120,
      render: (val: number) => (
        <span style={{ color: val > 0 ? "#cf1322" : "#3f8600" }}>
          {val > 0 ? "+" : ""}
          {val.toFixed(2)}
        </span>
      ),
    },
    {
      title: "Change %",
      dataIndex: "change_percent",
      key: "change_percent",
      width: 120,
      render: (val: number) => (
        <Space>
          {val > 0 ? <ArrowUpOutlined style={{ color: "#cf1322" }} /> : <ArrowDownOutlined style={{ color: "#3f8600" }} />}
          <span style={{ color: val > 0 ? "#cf1322" : "#3f8600" }}>
            {val > 0 ? "+" : ""}
            {val.toFixed(1)}%
          </span>
        </Space>
      ),
    },
    {
      title: "Status",
      key: "status",
      width: 120,
      render: (_: any, record: any) => {
        if (record.regression) {
          return <Tag color="red">REGRESSION</Tag>;
        } else if (record.improvement) {
          return <Tag color="green">IMPROVED</Tag>;
        } else {
          return <Tag color="blue">STABLE</Tag>;
        }
      },
    },
  ];

  const hasRegressions = tableData.some((row) => row.regression);

  return (
    <Space direction="vertical" style={{ width: "100%" }} size="large">
      {/* Overall trend */}
      <Card>
        <Row gutter={16}>
          <Col span={8}>
            <Statistic
              title="Overall Trend"
              value={trend}
              valueStyle={{ color: getTrendColor(trend) }}
              prefix={
                trend === "degrading" ? (
                  <WarningOutlined />
                ) : trend === "improving" ? (
                  <CheckCircleOutlined />
                ) : null
              }
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="Current Executions"
              value={current.executions}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="Historical Samples"
              value={historical?.sample_count || 0}
            />
          </Col>
        </Row>
      </Card>

      {/* Alert for regressions */}
      {hasRegressions && (
        <Alert
          message="Performance Regression Detected"
          description="One or more metrics have regressed beyond the threshold. Review the comparison table and recommendations below."
          type="error"
          showIcon
          icon={<WarningOutlined />}
        />
      )}

      {/* Comparison table */}
      <Card title="Performance Comparison">
        <Table
          dataSource={tableData}
          columns={columns}
          rowKey="metric"
          size="small"
          pagination={false}
          scroll={{ x: true }}
        />
      </Card>

      {/* Current metrics */}
      <Card title="Current Performance Metrics" size="small">
        <Descriptions bordered size="small" column={2}>
          <Descriptions.Item label="Executions">
            {current.executions}
          </Descriptions.Item>
          <Descriptions.Item label="Elapsed Time (sec)">
            {current.elapsed_time_sec.toFixed(4)}
          </Descriptions.Item>
          <Descriptions.Item label="CPU Time (sec)">
            {current.cpu_time_sec.toFixed(4)}
          </Descriptions.Item>
          <Descriptions.Item label="Buffer Gets per Exec">
            {current.buffer_gets_per_exec.toFixed(2)}
          </Descriptions.Item>
          <Descriptions.Item label="Disk Reads per Exec">
            {current.disk_reads_per_exec.toFixed(2)}
          </Descriptions.Item>
          <Descriptions.Item label="Rows per Exec">
            {current.rows_processed_per_exec.toFixed(2)}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* Recommendations */}
      {recommendations && recommendations.length > 0 && (
        <Alert
          message="Recommendations"
          description={
            <ul style={{ marginBottom: 0 }}>
              {recommendations.map((rec, index) => (
                <li key={index}>{rec}</li>
              ))}
            </ul>
          }
          type="info"
          showIcon
        />
      )}
    </Space>
  );
};
