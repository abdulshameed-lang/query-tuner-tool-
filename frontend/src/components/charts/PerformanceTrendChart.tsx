/**
 * Performance trend chart with trend indicators
 */

import React from "react";
import { Card, Space, Tag, Alert } from "antd";
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  MinusOutlined,
} from "@ant-design/icons";
import { TimeSeriesChart } from "./TimeSeriesChart";
import type { PerformanceTrendResult, PerformanceAnomaly } from "../../types/awrAsh";
import { getTrendColor } from "../../api/awrAsh";

interface PerformanceTrendChartProps {
  trendData: PerformanceTrendResult;
  metricKey?: string;
  metricName?: string;
}

export const PerformanceTrendChart: React.FC<PerformanceTrendChartProps> = ({
  trendData,
  metricKey = "elapsed_time_sec",
  metricName = "Elapsed Time (sec)",
}) => {
  const { time_series, metrics_trends, overall_trend, anomalies } = trendData;

  // Get trend for the selected metric
  const metricTrend = metrics_trends[metricKey];

  // Get trend icon
  const getTrendIcon = () => {
    if (!metricTrend) return null;

    switch (metricTrend.direction) {
      case "increasing":
        return <ArrowUpOutlined style={{ color: "red" }} />;
      case "decreasing":
        return <ArrowDownOutlined style={{ color: "green" }} />;
      case "stable":
        return <MinusOutlined style={{ color: "blue" }} />;
      default:
        return null;
    }
  };

  // Get anomalies for this metric
  const metricAnomalies = anomalies.filter((a) => a.metric === metricKey);

  return (
    <Space direction="vertical" style={{ width: "100%" }} size="large">
      {/* Overall trend indicator */}
      <Card size="small">
        <Space>
          <span>Overall Trend:</span>
          <Tag color={getTrendColor(overall_trend)}>
            {overall_trend.toUpperCase()}
          </Tag>
          {metricTrend && (
            <>
              <span>Direction:</span>
              {getTrendIcon()}
              <span>{metricTrend.direction}</span>
              <span>(slope: {metricTrend.slope.toFixed(4)})</span>
            </>
          )}
        </Space>
      </Card>

      {/* Anomaly alerts */}
      {metricAnomalies.length > 0 && (
        <Alert
          message={`${metricAnomalies.length} Anomal${metricAnomalies.length > 1 ? "ies" : "y"} Detected`}
          description={
            <Space direction="vertical" size="small">
              {metricAnomalies.slice(0, 3).map((anomaly, index) => (
                <div key={index}>
                  <Tag color={anomaly.severity === "high" ? "red" : "orange"}>
                    {anomaly.severity.toUpperCase()}
                  </Tag>
                  {new Date(anomaly.timestamp).toLocaleString()}: {anomaly.value.toFixed(2)}
                  (z-score: {anomaly.z_score})
                </div>
              ))}
              {metricAnomalies.length > 3 && (
                <div>...and {metricAnomalies.length - 3} more</div>
              )}
            </Space>
          }
          type="warning"
          showIcon
        />
      )}

      {/* Time series chart */}
      <TimeSeriesChart
        data={time_series}
        lines={[
          {
            dataKey: metricKey,
            name: metricName,
            color: "#1890ff",
          },
        ]}
        title={`${metricName} Trend`}
        xAxisLabel="Time"
        yAxisLabel={metricName}
      />
    </Space>
  );
};
