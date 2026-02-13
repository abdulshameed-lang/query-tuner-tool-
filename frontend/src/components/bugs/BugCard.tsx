/**
 * Bug card component - displays individual bug information
 */

import React from "react";
import { Card, Tag, Space, Typography, Button, Tooltip } from "antd";
import {
  BugOutlined,
  WarningOutlined,
  InfoCircleOutlined,
  LinkOutlined,
} from "@ant-design/icons";
import type { Bug, BugMatch } from "../../types/bug";
import {
  getSeverityColor,
  getConfidenceColor,
  getConfidenceLevel,
  formatBugNumber,
} from "../../api/bugs";

const { Text, Paragraph } = Typography;

interface BugCardProps {
  bug: Bug;
  match?: BugMatch;
  onClick?: () => void;
  showConfidence?: boolean;
}

export const BugCard: React.FC<BugCardProps> = ({
  bug,
  match,
  onClick,
  showConfidence = false,
}) => {
  const confidence = match?.confidence;
  const hasMatch = !!match;

  return (
    <Card
      hoverable={!!onClick}
      onClick={onClick}
      style={{ marginBottom: 16 }}
      title={
        <Space>
          <BugOutlined />
          <Text strong>{formatBugNumber(bug.bug_number)}</Text>
          <Tag color={getSeverityColor(bug.severity)}>
            {bug.severity.toUpperCase()}
          </Tag>
          {showConfidence && confidence !== undefined && (
            <Tag color={getConfidenceColor(confidence)}>
              {confidence}% {getConfidenceLevel(confidence)}
            </Tag>
          )}
        </Space>
      }
      extra={
        bug.my_oracle_support_url && (
          <Tooltip title="View on My Oracle Support">
            <Button
              type="link"
              icon={<LinkOutlined />}
              href={bug.my_oracle_support_url}
              target="_blank"
              onClick={(e) => e.stopPropagation()}
            >
              MOS
            </Button>
          </Tooltip>
        )
      }
    >
      <Space direction="vertical" style={{ width: "100%" }} size="small">
        {/* Title */}
        <Text strong style={{ fontSize: 16 }}>
          {bug.title}
        </Text>

        {/* Category */}
        <Space>
          <Tag color="blue">{bug.category}</Tag>
        </Space>

        {/* Description */}
        <Paragraph
          ellipsis={{ rows: 2, expandable: true, symbol: "more" }}
          style={{ marginBottom: 8 }}
        >
          {bug.description}
        </Paragraph>

        {/* Affected/Fixed Versions */}
        <Space direction="vertical" size={4}>
          <Space size={4}>
            <WarningOutlined style={{ color: "#ff4d4f" }} />
            <Text type="secondary" style={{ fontSize: 12 }}>
              Affected: {bug.affected_versions.join(", ")}
            </Text>
          </Space>
          <Space size={4}>
            <InfoCircleOutlined style={{ color: "#52c41a" }} />
            <Text type="secondary" style={{ fontSize: 12 }}>
              Fixed: {bug.fixed_versions.length > 0 ? bug.fixed_versions.join(", ") : "No fix available"}
            </Text>
          </Space>
        </Space>

        {/* Matched patterns if this is a match */}
        {hasMatch && match.matched_patterns && match.matched_patterns.length > 0 && (
          <Space wrap size={4}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              Matched patterns:
            </Text>
            {match.matched_patterns.map((pattern) => (
              <Tag key={pattern} color="purple" style={{ fontSize: 11 }}>
                {pattern}
              </Tag>
            ))}
          </Space>
        )}

        {/* Workarounds count */}
        {bug.workarounds && bug.workarounds.length > 0 && (
          <Text type="secondary" style={{ fontSize: 12 }}>
            {bug.workarounds.length} workaround(s) available
          </Text>
        )}
      </Space>
    </Card>
  );
};
