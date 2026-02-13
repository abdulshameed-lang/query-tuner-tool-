/**
 * Bug list component - displays filterable list of bugs
 */

import React, { useState } from "react";
import {
  Space,
  Select,
  Input,
  Empty,
  Spin,
  Alert,
  Row,
  Col,
  Statistic,
  Card,
} from "antd";
import { SearchOutlined, BugOutlined } from "@ant-design/icons";
import type { Bug, BugMatch, BugFilters } from "../../types/bug";
import { BugCard } from "./BugCard";
import { BugDetailsModal } from "./BugDetailsModal";
import { BugSeverity, BugCategory } from "../../types/bug";

const { Option } = Select;

interface BugListProps {
  bugs: Bug[];
  matches?: BugMatch[];
  loading?: boolean;
  error?: Error | null;
  onFilterChange?: (filters: BugFilters) => void;
  showConfidence?: boolean;
  showStats?: boolean;
}

export const BugList: React.FC<BugListProps> = ({
  bugs,
  matches,
  loading = false,
  error = null,
  onFilterChange,
  showConfidence = false,
  showStats = true,
}) => {
  const [selectedBug, setSelectedBug] = useState<Bug | null>(null);
  const [selectedMatch, setSelectedMatch] = useState<BugMatch | undefined>(
    undefined
  );
  const [modalVisible, setModalVisible] = useState(false);
  const [filters, setFilters] = useState<BugFilters>({});
  const [searchText, setSearchText] = useState("");

  const handleFilterChange = (key: keyof BugFilters, value: string | undefined) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    onFilterChange?.(newFilters);
  };

  const handleBugClick = (bug: Bug, match?: BugMatch) => {
    setSelectedBug(bug);
    setSelectedMatch(match);
    setModalVisible(true);
  };

  const handleModalClose = () => {
    setModalVisible(false);
    setSelectedBug(null);
    setSelectedMatch(undefined);
  };

  // Filter bugs based on search text
  const filteredBugs = bugs.filter((bug) => {
    if (!searchText) return true;
    const searchLower = searchText.toLowerCase();
    return (
      bug.title.toLowerCase().includes(searchLower) ||
      bug.bug_number.includes(searchLower) ||
      bug.description.toLowerCase().includes(searchLower)
    );
  });

  // Calculate statistics
  const stats = {
    total: filteredBugs.length,
    critical: filteredBugs.filter((b) => b.severity === BugSeverity.CRITICAL).length,
    high: filteredBugs.filter((b) => b.severity === BugSeverity.HIGH).length,
    medium: filteredBugs.filter((b) => b.severity === BugSeverity.MEDIUM).length,
    low: filteredBugs.filter((b) => b.severity === BugSeverity.LOW).length,
  };

  if (error) {
    return (
      <Alert
        message="Error Loading Bugs"
        description={error.message}
        type="error"
        showIcon
      />
    );
  }

  return (
    <div>
      {/* Filters */}
      <Card style={{ marginBottom: 16 }}>
        <Space direction="vertical" style={{ width: "100%" }} size="middle">
          <Row gutter={16}>
            <Col xs={24} sm={12} md={8}>
              <Input
                placeholder="Search bugs..."
                prefix={<SearchOutlined />}
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                allowClear
              />
            </Col>
            <Col xs={24} sm={12} md={8}>
              <Select
                placeholder="Filter by severity"
                style={{ width: "100%" }}
                allowClear
                onChange={(value) => handleFilterChange("severity", value)}
              >
                <Option value={BugSeverity.CRITICAL}>Critical</Option>
                <Option value={BugSeverity.HIGH}>High</Option>
                <Option value={BugSeverity.MEDIUM}>Medium</Option>
                <Option value={BugSeverity.LOW}>Low</Option>
              </Select>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <Select
                placeholder="Filter by category"
                style={{ width: "100%" }}
                allowClear
                onChange={(value) => handleFilterChange("category", value)}
              >
                <Option value={BugCategory.OPTIMIZER}>Optimizer</Option>
                <Option value={BugCategory.EXECUTION}>Execution</Option>
                <Option value={BugCategory.STATISTICS}>Statistics</Option>
                <Option value={BugCategory.PARALLEL}>Parallel</Option>
                <Option value={BugCategory.PARTITIONING}>Partitioning</Option>
                <Option value={BugCategory.PARSING}>Parsing</Option>
                <Option value={BugCategory.MEMORY}>Memory</Option>
                <Option value={BugCategory.LOCKING}>Locking</Option>
                <Option value={BugCategory.NETWORK}>Network</Option>
                <Option value={BugCategory.OTHER}>Other</Option>
              </Select>
            </Col>
          </Row>

          {/* Statistics */}
          {showStats && (
            <Row gutter={16}>
              <Col xs={12} sm={6} md={4}>
                <Statistic
                  title="Total"
                  value={stats.total}
                  prefix={<BugOutlined />}
                />
              </Col>
              <Col xs={12} sm={6} md={4}>
                <Statistic
                  title="Critical"
                  value={stats.critical}
                  valueStyle={{ color: "#cf1322" }}
                />
              </Col>
              <Col xs={12} sm={6} md={4}>
                <Statistic
                  title="High"
                  value={stats.high}
                  valueStyle={{ color: "#d46b08" }}
                />
              </Col>
              <Col xs={12} sm={6} md={4}>
                <Statistic
                  title="Medium"
                  value={stats.medium}
                  valueStyle={{ color: "#d4b106" }}
                />
              </Col>
              <Col xs={12} sm={6} md={4}>
                <Statistic
                  title="Low"
                  value={stats.low}
                  valueStyle={{ color: "#1890ff" }}
                />
              </Col>
            </Row>
          )}
        </Space>
      </Card>

      {/* Bug list */}
      <Spin spinning={loading}>
        {filteredBugs.length === 0 ? (
          <Empty
            description="No bugs found"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        ) : (
          <div>
            {filteredBugs.map((bug) => {
              const match = matches?.find((m) => m.bug.bug_number === bug.bug_number);
              return (
                <BugCard
                  key={bug.bug_number}
                  bug={bug}
                  match={match}
                  onClick={() => handleBugClick(bug, match)}
                  showConfidence={showConfidence}
                />
              );
            })}
          </div>
        )}
      </Spin>

      {/* Details modal */}
      <BugDetailsModal
        bug={selectedBug}
        match={selectedMatch}
        visible={modalVisible}
        onClose={handleModalClose}
      />
    </div>
  );
};
