/**
 * Time-series chart component for displaying metrics over time
 */

import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { Card, Empty } from "antd";
import type { LineChartData } from "../../types/awrAsh";

interface TimeSeriesChartProps {
  data: any[];
  lines: {
    dataKey: string;
    name: string;
    color: string;
    yAxisId?: string;
  }[];
  title?: string;
  height?: number;
  xAxisKey?: string;
  xAxisLabel?: string;
  yAxisLabel?: string;
  showLegend?: boolean;
  showGrid?: boolean;
}

export const TimeSeriesChart: React.FC<TimeSeriesChartProps> = ({
  data,
  lines,
  title,
  height = 400,
  xAxisKey = "timestamp",
  xAxisLabel,
  yAxisLabel,
  showLegend = true,
  showGrid = true,
}) => {
  if (!data || data.length === 0) {
    return (
      <Card title={title}>
        <Empty description="No data available" />
      </Card>
    );
  }

  // Format timestamp for display
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };

  return (
    <Card title={title}>
      <ResponsiveContainer width="100%" height={height}>
        <LineChart
          data={data}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          {showGrid && <CartesianGrid strokeDasharray="3 3" />}
          <XAxis
            dataKey={xAxisKey}
            tickFormatter={formatTimestamp}
            label={xAxisLabel ? { value: xAxisLabel, position: "insideBottom", offset: -5 } : undefined}
          />
          <YAxis
            label={yAxisLabel ? { value: yAxisLabel, angle: -90, position: "insideLeft" } : undefined}
          />
          <Tooltip
            labelFormatter={formatTimestamp}
            formatter={(value: any) => {
              if (typeof value === "number") {
                return value.toFixed(2);
              }
              return value;
            }}
          />
          {showLegend && <Legend />}
          {lines.map((line) => (
            <Line
              key={line.dataKey}
              type="monotone"
              dataKey={line.dataKey}
              stroke={line.color}
              name={line.name}
              yAxisId={line.yAxisId || 0}
              dot={false}
              strokeWidth={2}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </Card>
  );
};
