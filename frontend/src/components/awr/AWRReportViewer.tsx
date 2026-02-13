/**
 * AWR Report Viewer component
 */

import React from "react";
import {
  Card,
  Descriptions,
  Table,
  Space,
  Typography,
  Divider,
  Alert,
  Tabs,
  Row,
  Col,
  Statistic,
} from "antd";
import {
  ClockCircleOutlined,
  ThunderboltOutlined,
  DatabaseOutlined,
} from "@ant-design/icons";
import type { AWRReport, TopSQL, WaitEvent } from "../../types/awrAsh";

const { Title, Text } = Typography;
const { TabPane } = Tabs;

interface AWRReportViewerProps {
  report: AWRReport;
}

export const AWRReportViewer: React.FC<AWRReportViewerProps> = ({ report }) => {
  const {
    report_info,
    database_info,
    top_sql_by_elapsed_time,
    top_sql_by_cpu,
    top_sql_by_gets,
    wait_events,
    wait_events_summary,
    instance_efficiency,
    recommendations,
  } = report;

  // Top SQL columns
  const topSQLColumns = [
    {
      title: "SQL_ID",
      dataIndex: "sql_id",
      key: "sql_id",
      width: 150,
    },
    {
      title: "Executions",
      dataIndex: "executions",
      key: "executions",
      width: 120,
      render: (val: number) => val.toLocaleString(),
    },
    {
      title: "Elapsed Time (s)",
      dataIndex: "elapsed_time_sec",
      key: "elapsed_time_sec",
      width: 150,
      render: (val: number) => val.toFixed(2),
      sorter: (a: TopSQL, b: TopSQL) => a.elapsed_time_sec - b.elapsed_time_sec,
    },
    {
      title: "CPU Time (s)",
      dataIndex: "cpu_time_sec",
      key: "cpu_time_sec",
      width: 130,
      render: (val: number) => val.toFixed(2),
    },
    {
      title: "Buffer Gets",
      dataIndex: "buffer_gets",
      key: "buffer_gets",
      width: 130,
      render: (val: number) => val.toLocaleString(),
    },
    {
      title: "Avg Elapsed (s)",
      dataIndex: "avg_elapsed_sec",
      key: "avg_elapsed_sec",
      width: 140,
      render: (val: number) => val.toFixed(4),
    },
  ];

  // Wait events columns
  const waitEventsColumns = [
    {
      title: "Event Name",
      dataIndex: "event_name",
      key: "event_name",
    },
    {
      title: "Wait Class",
      dataIndex: "wait_class",
      key: "wait_class",
      width: 150,
    },
    {
      title: "Total Waits",
      dataIndex: "total_waits_delta",
      key: "total_waits_delta",
      width: 130,
      render: (val: number) => val.toLocaleString(),
    },
    {
      title: "Time Waited (s)",
      dataIndex: "time_waited_sec",
      key: "time_waited_sec",
      width: 150,
      render: (val: number) => val.toFixed(2),
      sorter: (a: WaitEvent, b: WaitEvent) => a.time_waited_sec - b.time_waited_sec,
    },
    {
      title: "Avg Wait (ms)",
      dataIndex: "avg_wait_ms",
      key: "avg_wait_ms",
      width: 130,
      render: (val: number) => val.toFixed(2),
    },
  ];

  return (
    <Space direction="vertical" style={{ width: "100%" }} size="large">
      {/* Report Header */}
      <Card>
        <Title level={3}>
          <DatabaseOutlined /> AWR Performance Report
        </Title>
        <Descriptions bordered size="small" column={2}>
          <Descriptions.Item label="Begin Snapshot">
            {report_info.begin_snap_id} ({new Date(report_info.begin_time).toLocaleString()})
          </Descriptions.Item>
          <Descriptions.Item label="End Snapshot">
            {report_info.end_snap_id} ({new Date(report_info.end_time).toLocaleString()})
          </Descriptions.Item>
          <Descriptions.Item label="Elapsed Time">
            {report_info.elapsed_time_minutes.toFixed(2)} minutes
          </Descriptions.Item>
          <Descriptions.Item label="Generated At">
            {new Date(report_info.generated_at).toLocaleString()}
          </Descriptions.Item>
          {database_info.instance_name && (
            <Descriptions.Item label="Instance">
              {database_info.instance_name}
            </Descriptions.Item>
          )}
          {database_info.host_name && (
            <Descriptions.Item label="Host">
              {database_info.host_name}
            </Descriptions.Item>
          )}
        </Descriptions>
      </Card>

      {/* Recommendations */}
      {recommendations && recommendations.length > 0 && (
        <Alert
          message="Performance Recommendations"
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

      {/* Instance Efficiency */}
      {instance_efficiency && (
        <Card title="Instance Efficiency Percentages">
          <Row gutter={16}>
            <Col span={8}>
              <Statistic
                title="Buffer Cache Hit Ratio"
                value={instance_efficiency.buffer_cache_hit_ratio || 0}
                precision={2}
                suffix="%"
                valueStyle={{
                  color:
                    (instance_efficiency.buffer_cache_hit_ratio || 0) > 90
                      ? "#3f8600"
                      : "#cf1322",
                }}
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="Soft Parse Ratio"
                value={instance_efficiency.soft_parse_ratio || 0}
                precision={2}
                suffix="%"
                valueStyle={{
                  color:
                    (instance_efficiency.soft_parse_ratio || 0) > 80
                      ? "#3f8600"
                      : "#cf1322",
                }}
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="Execute to Parse Ratio"
                value={instance_efficiency.execute_to_parse_ratio || 0}
                precision={2}
              />
            </Col>
          </Row>
        </Card>
      )}

      {/* Top SQL Tabs */}
      <Card title={<><ThunderboltOutlined /> Top SQL Statements</>}>
        <Tabs defaultActiveKey="elapsed">
          <TabPane tab="By Elapsed Time" key="elapsed">
            <Table
              dataSource={top_sql_by_elapsed_time}
              columns={topSQLColumns}
              rowKey="sql_id"
              size="small"
              pagination={false}
              scroll={{ x: true }}
            />
          </TabPane>
          <TabPane tab="By CPU Time" key="cpu">
            <Table
              dataSource={top_sql_by_cpu}
              columns={topSQLColumns}
              rowKey="sql_id"
              size="small"
              pagination={false}
              scroll={{ x: true }}
            />
          </TabPane>
          <TabPane tab="By Buffer Gets" key="gets">
            <Table
              dataSource={top_sql_by_gets}
              columns={topSQLColumns}
              rowKey="sql_id"
              size="small"
              pagination={false}
              scroll={{ x: true }}
            />
          </TabPane>
        </Tabs>
      </Card>

      {/* Wait Events */}
      <Card title={<><ClockCircleOutlined /> Wait Events</>}>
        {wait_events_summary && (
          <Space direction="vertical" style={{ width: "100%", marginBottom: 16 }}>
            <Text>
              <Text strong>Total Wait Time:</Text>{" "}
              {wait_events_summary.total_wait_time_sec.toFixed(2)} seconds
            </Text>
            {wait_events_summary.top_wait_class && (
              <Text>
                <Text strong>Top Wait Class:</Text>{" "}
                {wait_events_summary.top_wait_class}
              </Text>
            )}
          </Space>
        )}
        <Table
          dataSource={wait_events}
          columns={waitEventsColumns}
          rowKey="event_name"
          size="small"
          pagination={{ pageSize: 10 }}
          scroll={{ x: true }}
        />
      </Card>
    </Space>
  );
};
