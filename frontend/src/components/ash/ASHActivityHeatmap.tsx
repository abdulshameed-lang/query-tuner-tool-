/**
 * ASH Activity Heatmap component
 */

import React from "react";
import { Card, Empty } from "antd";
import type { ASHHeatmapDataPoint } from "../../types/awrAsh";
import { getWaitClassColor } from "../../api/awrAsh";

interface ASHActivityHeatmapProps {
  data: ASHHeatmapDataPoint[];
  title?: string;
  height?: number;
}

export const ASHActivityHeatmap: React.FC<ASHActivityHeatmapProps> = ({
  data,
  title = "ASH Activity Heatmap",
  height = 400,
}) => {
  if (!data || data.length === 0) {
    return (
      <Card title={title}>
        <Empty description="No activity data available" />
      </Card>
    );
  }

  // Group data by timestamp and wait class
  const timeSlots = Array.from(new Set(data.map((d) => d.timestamp))).sort();
  const waitClasses = Array.from(new Set(data.map((d) => d.wait_class)));

  // Create matrix
  const matrix: { [key: string]: { [key: string]: number } } = {};
  timeSlots.forEach((time) => {
    matrix[time] = {};
    waitClasses.forEach((wc) => {
      matrix[time][wc] = 0;
    });
  });

  // Fill matrix
  data.forEach((point) => {
    if (matrix[point.timestamp]) {
      matrix[point.timestamp][point.wait_class] = point.activity_count;
    }
  });

  // Get max value for scaling
  const maxValue = Math.max(...data.map((d) => d.activity_count));

  return (
    <Card title={title}>
      <div style={{ overflowX: "auto" }}>
        <table style={{ borderCollapse: "collapse", fontSize: "12px" }}>
          <thead>
            <tr>
              <th style={{ padding: "8px", border: "1px solid #ddd" }}>
                Time
              </th>
              {waitClasses.map((wc) => (
                <th
                  key={wc}
                  style={{
                    padding: "8px",
                    border: "1px solid #ddd",
                    backgroundColor: getWaitClassColor(wc),
                    color: "white",
                    minWidth: "80px",
                  }}
                >
                  {wc}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {timeSlots.map((time) => (
              <tr key={time}>
                <td style={{ padding: "8px", border: "1px solid #ddd" }}>
                  {new Date(time).toLocaleTimeString()}
                </td>
                {waitClasses.map((wc) => {
                  const value = matrix[time][wc];
                  const intensity = maxValue > 0 ? value / maxValue : 0;
                  const backgroundColor = `rgba(24, 144, 255, ${intensity})`;

                  return (
                    <td
                      key={wc}
                      style={{
                        padding: "8px",
                        border: "1px solid #ddd",
                        backgroundColor,
                        textAlign: "center",
                        color: intensity > 0.5 ? "white" : "black",
                      }}
                      title={`${wc}: ${value} samples`}
                    >
                      {value > 0 ? value : ""}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
};
