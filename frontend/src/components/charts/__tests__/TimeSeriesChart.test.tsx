/**
 * Unit tests for TimeSeriesChart component
 */

import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { TimeSeriesChart } from "../TimeSeriesChart";

describe("TimeSeriesChart", () => {
  const mockData = [
    {
      timestamp: "2024-01-15T10:00:00",
      elapsed_time_sec: 1.5,
      cpu_time_sec: 0.5,
    },
    {
      timestamp: "2024-01-15T10:01:00",
      elapsed_time_sec: 1.8,
      cpu_time_sec: 0.6,
    },
    {
      timestamp: "2024-01-15T10:02:00",
      elapsed_time_sec: 1.2,
      cpu_time_sec: 0.4,
    },
  ];

  const mockLines = [
    {
      dataKey: "elapsed_time_sec",
      name: "Elapsed Time (sec)",
      color: "#1890ff",
    },
    {
      dataKey: "cpu_time_sec",
      name: "CPU Time (sec)",
      color: "#52c41a",
    },
  ];

  it("renders chart with data", () => {
    render(<TimeSeriesChart data={mockData} lines={mockLines} title="Performance Metrics" />);

    expect(screen.getByText("Performance Metrics")).toBeInTheDocument();
  });

  it("renders empty state when no data provided", () => {
    render(<TimeSeriesChart data={[]} lines={mockLines} title="No Data Chart" />);

    expect(screen.getByText("No Data Chart")).toBeInTheDocument();
    expect(screen.getByText("No data available")).toBeInTheDocument();
  });

  it("renders chart without title", () => {
    const { container } = render(<TimeSeriesChart data={mockData} lines={mockLines} />);

    // Chart should still render
    expect(container.querySelector(".recharts-wrapper")).toBeInTheDocument();
  });

  it("applies custom height", () => {
    const { container } = render(
      <TimeSeriesChart data={mockData} lines={mockLines} height={300} />
    );

    const responsiveContainer = container.querySelector(".recharts-responsive-container");
    expect(responsiveContainer).toHaveStyle({ height: "300px" });
  });

  it("renders legend when showLegend is true", () => {
    const { container } = render(
      <TimeSeriesChart data={mockData} lines={mockLines} showLegend={true} />
    );

    expect(container.querySelector(".recharts-legend-wrapper")).toBeInTheDocument();
  });

  it("does not render legend when showLegend is false", () => {
    const { container } = render(
      <TimeSeriesChart data={mockData} lines={mockLines} showLegend={false} />
    );

    expect(container.querySelector(".recharts-legend-wrapper")).not.toBeInTheDocument();
  });

  it("renders grid when showGrid is true", () => {
    const { container } = render(
      <TimeSeriesChart data={mockData} lines={mockLines} showGrid={true} />
    );

    expect(container.querySelector(".recharts-cartesian-grid")).toBeInTheDocument();
  });

  it("does not render grid when showGrid is false", () => {
    const { container } = render(
      <TimeSeriesChart data={mockData} lines={mockLines} showGrid={false} />
    );

    expect(container.querySelector(".recharts-cartesian-grid")).not.toBeInTheDocument();
  });

  it("renders all specified lines", () => {
    const { container } = render(<TimeSeriesChart data={mockData} lines={mockLines} />);

    const lines = container.querySelectorAll(".recharts-line");
    expect(lines.length).toBe(mockLines.length);
  });

  it("uses custom xAxisKey", () => {
    render(
      <TimeSeriesChart
        data={mockData}
        lines={mockLines}
        xAxisKey="timestamp"
      />
    );

    // Chart should render successfully with custom key
    const { container } = render(<TimeSeriesChart data={mockData} lines={mockLines} />);
    expect(container.querySelector(".recharts-wrapper")).toBeInTheDocument();
  });

  it("handles single data point", () => {
    const singlePoint = [mockData[0]];

    render(<TimeSeriesChart data={singlePoint} lines={mockLines} />);

    const { container } = render(<TimeSeriesChart data={singlePoint} lines={mockLines} />);
    expect(container.querySelector(".recharts-wrapper")).toBeInTheDocument();
  });

  it("handles empty lines array", () => {
    render(<TimeSeriesChart data={mockData} lines={[]} />);

    // Should render chart structure even with no lines
    const { container } = render(<TimeSeriesChart data={mockData} lines={[]} />);
    expect(container.querySelector(".recharts-wrapper")).toBeInTheDocument();
  });
});
