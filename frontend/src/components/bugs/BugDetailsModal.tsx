/**
 * Bug details modal - displays comprehensive bug information
 */

import React from "react";
import {
  Modal,
  Descriptions,
  Tag,
  Space,
  Typography,
  List,
  Button,
  Card,
  Alert,
  Divider,
  Collapse,
} from "antd";
import {
  CopyOutlined,
  LinkOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  BulbOutlined,
  CodeOutlined,
} from "@ant-design/icons";
import type { Bug, BugMatch } from "../../types/bug";
import {
  getSeverityColor,
  getConfidenceColor,
  getConfidenceLevel,
  formatBugNumber,
} from "../../api/bugs";

const { Text, Paragraph, Title } = Typography;
const { Panel } = Collapse;

interface BugDetailsModalProps {
  bug: Bug | null;
  match?: BugMatch;
  visible: boolean;
  onClose: () => void;
}

export const BugDetailsModal: React.FC<BugDetailsModalProps> = ({
  bug,
  match,
  visible,
  onClose,
}) => {
  if (!bug) return null;

  const handleCopySQL = () => {
    if (bug.remediation_sql) {
      navigator.clipboard.writeText(bug.remediation_sql);
    }
  };

  const confidence = match?.confidence;
  const hasMatch = !!match;

  return (
    <Modal
      title={
        <Space>
          {formatBugNumber(bug.bug_number)} - {bug.title}
        </Space>
      }
      open={visible}
      onCancel={onClose}
      width={900}
      footer={[
        bug.my_oracle_support_url && (
          <Button
            key="mos"
            icon={<LinkOutlined />}
            href={bug.my_oracle_support_url}
            target="_blank"
          >
            View on My Oracle Support
          </Button>
        ),
        <Button key="close" type="primary" onClick={onClose}>
          Close
        </Button>,
      ]}
    >
      <Space direction="vertical" style={{ width: "100%" }} size="large">
        {/* Header tags */}
        <Space wrap>
          <Tag color={getSeverityColor(bug.severity)} style={{ fontSize: 14 }}>
            {bug.severity.toUpperCase()}
          </Tag>
          <Tag color="blue" style={{ fontSize: 14 }}>
            {bug.category}
          </Tag>
          {hasMatch && confidence !== undefined && (
            <Tag color={getConfidenceColor(confidence)} style={{ fontSize: 14 }}>
              {confidence}% Confidence ({getConfidenceLevel(confidence)})
            </Tag>
          )}
        </Space>

        {/* High confidence alert */}
        {hasMatch && confidence && confidence >= 75 && (
          <Alert
            message="High Confidence Match"
            description="This bug has been detected with high confidence. Review the evidence and consider applying the recommended workarounds."
            type="warning"
            showIcon
            icon={<WarningOutlined />}
          />
        )}

        {/* Description */}
        <Card size="small" title="Description">
          <Paragraph>{bug.description}</Paragraph>
        </Card>

        {/* Versions */}
        <Descriptions bordered size="small" column={1}>
          <Descriptions.Item
            label={
              <Space>
                <WarningOutlined style={{ color: "#ff4d4f" }} />
                <Text>Affected Versions</Text>
              </Space>
            }
          >
            <Space wrap>
              {bug.affected_versions.map((version) => (
                <Tag key={version} color="red">
                  {version}
                </Tag>
              ))}
            </Space>
          </Descriptions.Item>
          <Descriptions.Item
            label={
              <Space>
                <CheckCircleOutlined style={{ color: "#52c41a" }} />
                <Text>Fixed Versions</Text>
              </Space>
            }
          >
            {bug.fixed_versions.length > 0 ? (
              <Space wrap>
                {bug.fixed_versions.map((version) => (
                  <Tag key={version} color="green">
                    {version}
                  </Tag>
                ))}
              </Space>
            ) : (
              <Text type="secondary">No fix available yet</Text>
            )}
          </Descriptions.Item>
        </Descriptions>

        {/* Symptoms */}
        {bug.symptoms && bug.symptoms.length > 0 && (
          <Card
            size="small"
            title={
              <Space>
                <WarningOutlined />
                <Text>Symptoms</Text>
              </Space>
            }
          >
            <List
              size="small"
              dataSource={bug.symptoms}
              renderItem={(symptom) => (
                <List.Item>
                  <Text>• {symptom}</Text>
                </List.Item>
              )}
            />
          </Card>
        )}

        {/* Matched patterns and evidence */}
        {hasMatch && match.matched_patterns && match.matched_patterns.length > 0 && (
          <Card
            size="small"
            title={
              <Space>
                <CheckCircleOutlined style={{ color: "#52c41a" }} />
                <Text>Detection Evidence</Text>
              </Space>
            }
          >
            <Space direction="vertical" style={{ width: "100%" }}>
              <Space wrap>
                <Text strong>Matched Patterns:</Text>
                {match.matched_patterns.map((pattern) => (
                  <Tag key={pattern} color="purple">
                    {pattern}
                  </Tag>
                ))}
              </Space>

              {match.evidence && (
                <Collapse ghost>
                  {Object.entries(match.evidence).map(([key, value]) => (
                    value && (
                      <Panel header={`${key} Evidence`} key={key}>
                        <pre style={{ fontSize: 12, whiteSpace: "pre-wrap" }}>
                          {JSON.stringify(value, null, 2)}
                        </pre>
                      </Panel>
                    )
                  ))}
                </Collapse>
              )}
            </Space>
          </Card>
        )}

        {/* Workarounds */}
        {bug.workarounds && bug.workarounds.length > 0 && (
          <Card
            size="small"
            title={
              <Space>
                <BulbOutlined style={{ color: "#faad14" }} />
                <Text>Workarounds</Text>
              </Space>
            }
          >
            <List
              size="small"
              dataSource={bug.workarounds}
              renderItem={(workaround, index) => (
                <List.Item>
                  <Text>
                    <Text strong>{index + 1}.</Text> {workaround}
                  </Text>
                </List.Item>
              )}
            />
          </Card>
        )}

        {/* Remediation SQL */}
        {bug.remediation_sql && (
          <Card
            size="small"
            title={
              <Space>
                <CodeOutlined />
                <Text>Remediation SQL</Text>
              </Space>
            }
            extra={
              <Button
                type="link"
                icon={<CopyOutlined />}
                onClick={handleCopySQL}
                size="small"
              >
                Copy
              </Button>
            }
          >
            <pre
              style={{
                background: "#f5f5f5",
                padding: 12,
                borderRadius: 4,
                overflow: "auto",
              }}
            >
              <code>{bug.remediation_sql}</code>
            </pre>
          </Card>
        )}
      </Space>
    </Modal>
  );
};
