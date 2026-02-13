/**
 * Query bug detection component - displays bugs detected for a specific SQL_ID
 */

import React from "react";
import {
  Card,
  Alert,
  Spin,
  Empty,
  Space,
  Typography,
  Statistic,
  Row,
  Col,
  Divider,
} from "antd";
import {
  BugOutlined,
  WarningOutlined,
  SafetyOutlined,
  ClockCircleOutlined,
} from "@ant-design/icons";
import { BugList } from "./BugList";
import { useBugDetection } from "../../api/bugs";
import type { BugDetectionParams } from "../../types/bug";

const { Text, Title } = Typography;

interface QueryBugDetectionProps {
  sqlId: string;
  databaseVersion?: string;
}

export const QueryBugDetection: React.FC<QueryBugDetectionProps> = ({
  sqlId,
  databaseVersion,
}) => {
  const params: BugDetectionParams = {
    sql_id: sqlId,
    database_version: databaseVersion,
  };

  const { data, isLoading, error } = useBugDetection(params, !!sqlId);

  if (error) {
    return (
      <Card>
        <Alert
          message="Bug Detection Failed"
          description={error.message}
          type="error"
          showIcon
        />
      </Card>
    );
  }

  if (isLoading) {
    return (
      <Card>
        <Spin tip="Detecting bugs...">
          <div style={{ minHeight: 200 }} />
        </Spin>
      </Card>
    );
  }

  if (!data) {
    return null;
  }

  const { detected_bugs, summary, detection_timestamp } = data;
  const hasBugs = detected_bugs.length > 0;

  return (
    <Space direction="vertical" style={{ width: "100%" }} size="large">
      {/* Summary card */}
      <Card>
        <Space direction="vertical" style={{ width: "100%" }} size="middle">
          <Title level={4}>
            <BugOutlined /> Bug Detection Results
          </Title>

          {hasBugs ? (
            <>
              <Alert
                message={`${summary.total_bugs} Potential Bug${summary.total_bugs > 1 ? "s" : ""} Detected`}
                description={
                  summary.critical_count > 0
                    ? `${summary.critical_count} critical bug(s) found. Immediate action recommended.`
                    : summary.high_confidence_count > 0
                    ? `${summary.high_confidence_count} high confidence match(es). Review recommended.`
                    : "Review the detected bugs and consider applying workarounds."
                }
                type={summary.critical_count > 0 ? "error" : "warning"}
                showIcon
                icon={<WarningOutlined />}
              />

              {/* Statistics */}
              <Row gutter={16}>
                <Col xs={12} sm={6}>
                  <Statistic
                    title="Total Bugs"
                    value={summary.total_bugs}
                    prefix={<BugOutlined />}
                  />
                </Col>
                <Col xs={12} sm={6}>
                  <Statistic
                    title="Critical"
                    value={summary.critical_count}
                    valueStyle={{ color: "#cf1322" }}
                  />
                </Col>
                <Col xs={12} sm={6}>
                  <Statistic
                    title="High Confidence"
                    value={summary.high_confidence_count}
                    valueStyle={{ color: "#d46b08" }}
                  />
                </Col>
                <Col xs={12} sm={6}>
                  <Statistic
                    title="Detection Time"
                    value={new Date(detection_timestamp).toLocaleString()}
                    prefix={<ClockCircleOutlined />}
                    valueStyle={{ fontSize: 14 }}
                  />
                </Col>
              </Row>

              {/* Breakdown by severity */}
              {Object.keys(summary.by_severity).length > 0 && (
                <>
                  <Divider />
                  <Space direction="vertical" size="small">
                    <Text strong>By Severity:</Text>
                    <Space wrap>
                      {Object.entries(summary.by_severity).map(([severity, count]) => (
                        <Text key={severity}>
                          <Text type="secondary">{severity}:</Text> {count}
                        </Text>
                      ))}
                    </Space>
                  </Space>
                </>
              )}

              {/* Breakdown by category */}
              {Object.keys(summary.by_category).length > 0 && (
                <Space direction="vertical" size="small">
                  <Text strong>By Category:</Text>
                  <Space wrap>
                    {Object.entries(summary.by_category).map(([category, count]) => (
                      <Text key={category}>
                        <Text type="secondary">{category}:</Text> {count}
                      </Text>
                    ))}
                  </Space>
                </Space>
              )}
            </>
          ) : (
            <Alert
              message="No Bugs Detected"
              description="No known Oracle bugs were detected for this query. This is good news!"
              type="success"
              showIcon
              icon={<SafetyOutlined />}
            />
          )}

          {databaseVersion && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              Checked against Oracle version: {databaseVersion}
            </Text>
          )}
        </Space>
      </Card>

      {/* Bug list */}
      {hasBugs && (
        <BugList
          bugs={detected_bugs.map((match) => match.bug)}
          matches={detected_bugs}
          showConfidence={true}
          showStats={false}
        />
      )}
    </Space>
  );
};
