/**
 * Real-time monitoring dashboard
 */

import React, { useState } from "react";
import { Row, Col, Card, Badge, Space, Button, Typography } from "antd";
import {
  ReloadOutlined,
  PauseCircleOutlined,
  PlayCircleOutlined,
  WifiOutlined,
  DisconnectOutlined,
} from "@ant-design/icons";
import {
  useQueryMonitoring,
  useSessionMonitoring,
  useWaitEventsMonitoring,
  useMetricsMonitoring,
  WebSocketState,
} from "../hooks/useWebSocket";

const { Title, Text } = Typography;

export const RealtimeDashboard: React.FC = () => {
  const [paused, setPaused] = useState(false);

  // WebSocket connections
  const queries = useQueryMonitoring(5, 0.1, 10, !paused);
  const sessions = useSessionMonitoring(5, false, !paused);
  const waitEvents = useWaitEventsMonitoring(5, !paused);
  const metrics = useMetricsMonitoring(5, !paused);

  const togglePause = () => {
    if (paused) {
      queries.connect();
      sessions.connect();
      waitEvents.connect();
      metrics.connect();
    } else {
      queries.disconnect();
      sessions.disconnect();
      waitEvents.disconnect();
      metrics.disconnect();
    }
    setPaused(!paused);
  };

  const reconnectAll = () => {
    queries.reconnect();
    sessions.reconnect();
    waitEvents.reconnect();
    metrics.reconnect();
  };

  const getConnectionBadge = (state: WebSocketState) => {
    switch (state) {
      case WebSocketState.CONNECTED:
        return <Badge status="success" text="Connected" />;
      case WebSocketState.CONNECTING:
        return <Badge status="processing" text="Connecting..." />;
      case WebSocketState.DISCONNECTED:
        return <Badge status="default" text="Disconnected" />;
      case WebSocketState.ERROR:
        return <Badge status="error" text="Error" />;
    }
  };

  return (
    <div style={{ padding: 24 }}>
      <Space direction="vertical" style={{ width: "100%" }} size="large">
        {/* Header */}
        <Card>
          <Row justify="space-between" align="middle">
            <Col>
              <Title level={3} style={{ margin: 0 }}>
                <WifiOutlined /> Real-Time Monitoring Dashboard
              </Title>
            </Col>
            <Col>
              <Space>
                <Button
                  icon={paused ? <PlayCircleOutlined /> : <PauseCircleOutlined />}
                  onClick={togglePause}
                >
                  {paused ? "Resume" : "Pause"}
                </Button>
                <Button icon={<ReloadOutlined />} onClick={reconnectAll}>
                  Reconnect All
                </Button>
              </Space>
            </Col>
          </Row>
          <Row gutter={16} style={{ marginTop: 16 }}>
            <Col span={6}>
              <Text>Queries: {getConnectionBadge(queries.state)}</Text>
            </Col>
            <Col span={6}>
              <Text>Sessions: {getConnectionBadge(sessions.state)}</Text>
            </Col>
            <Col span={6}>
              <Text>Wait Events: {getConnectionBadge(waitEvents.state)}</Text>
            </Col>
            <Col span={6}>
              <Text>Metrics: {getConnectionBadge(metrics.state)}</Text>
            </Col>
          </Row>
        </Card>

        {/* Top Queries */}
        <Card title="Top Queries (Real-Time)" size="small">
          {queries.lastMessage?.data?.queries && (
            <div>
              {queries.lastMessage.data.queries.slice(0, 5).map((query: any) => (
                <div key={query.sql_id} style={{ marginBottom: 8 }}>
                  <Text strong>{query.sql_id}</Text> -{" "}
                  <Text>Elapsed: {(query.elapsed_time / 1000000).toFixed(2)}s</Text>
                  {queries.lastMessage.data.new_queries?.includes(query.sql_id) && (
                    <Badge status="success" text="NEW" style={{ marginLeft: 8 }} />
                  )}
                </div>
              ))}
            </div>
          )}
          {!queries.isConnected && (
            <Text type="secondary">Not connected</Text>
          )}
        </Card>

        {/* Active Sessions */}
        <Row gutter={16}>
          <Col span={12}>
            <Card title="Active Sessions" size="small">
              {sessions.lastMessage?.data && (
                <Space direction="vertical">
                  <Text>Total: {sessions.lastMessage.data.total_count}</Text>
                  <Text>Active: {sessions.lastMessage.data.active_count}</Text>
                  <Text>Blocked: {sessions.lastMessage.data.blocked_count}</Text>
                </Space>
              )}
              {!sessions.isConnected && (
                <Text type="secondary">Not connected</Text>
              )}
            </Card>
          </Col>

          {/* Database Metrics */}
          <Col span={12}>
            <Card title="Database Metrics" size="small">
              {metrics.lastMessage?.data?.metrics && (
                <div>
                  {Object.entries(metrics.lastMessage.data.metrics).slice(0, 5).map(([name, data]: [string, any]) => (
                    <div key={name}>
                      <Text>{name}: {data.rate_per_sec}/sec</Text>
                    </div>
                  ))}
                </div>
              )}
              {!metrics.isConnected && (
                <Text type="secondary">Not connected</Text>
              )}
            </Card>
          </Col>
        </Row>

        {/* Wait Events */}
        <Card title="Top Wait Events" size="small">
          {waitEvents.lastMessage?.data?.events && (
            <div>
              {waitEvents.lastMessage.data.events.slice(0, 5).map((event: any) => (
                <div key={event.event} style={{ marginBottom: 8 }}>
                  <Text strong>{event.event}</Text> - {event.wait_class} -{" "}
                  <Text>Delta: {event.delta_time_waited?.toFixed(2)}cs</Text>
                </div>
              ))}
            </div>
          )}
          {!waitEvents.isConnected && (
            <Text type="secondary">Not connected</Text>
          )}
        </Card>
      </Space>
    </div>
  );
};
