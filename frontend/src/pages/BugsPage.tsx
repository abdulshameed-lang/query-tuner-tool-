/**
 * Bugs page - main page for browsing Oracle bugs
 */

import React, { useState } from "react";
import {
  PageHeader,
  Card,
  Tabs,
  Alert,
  Space,
  Input,
  Button,
  Typography,
  Divider,
} from "antd";
import {
  BugOutlined,
  DatabaseOutlined,
  SearchOutlined,
  ReloadOutlined,
} from "@ant-design/icons";
import { BugList } from "../components/bugs/BugList";
import { useAllBugs, useVersionBugs } from "../api/bugs";
import type { BugFilters } from "../types/bug";

const { TabPane } = Tabs;
const { Text, Paragraph } = Typography;

export const BugsPage: React.FC = () => {
  const [filters, setFilters] = useState<BugFilters>({});
  const [versionInput, setVersionInput] = useState("");
  const [versionToCheck, setVersionToCheck] = useState("");

  // Fetch all bugs
  const {
    data: allBugsData,
    isLoading: allBugsLoading,
    error: allBugsError,
    refetch: refetchAllBugs,
  } = useAllBugs(filters);

  // Fetch version-specific bugs
  const {
    data: versionData,
    isLoading: versionLoading,
    error: versionError,
    refetch: refetchVersion,
  } = useVersionBugs(versionToCheck, !!versionToCheck);

  const handleVersionCheck = () => {
    if (versionInput.trim()) {
      setVersionToCheck(versionInput.trim());
    }
  };

  const handleFilterChange = (newFilters: BugFilters) => {
    setFilters(newFilters);
  };

  return (
    <div style={{ padding: 24 }}>
      <PageHeader
        title={
          <Space>
            <BugOutlined />
            <span>Oracle Bug Database</span>
          </Space>
        }
        subTitle="Browse and search known Oracle bugs"
        extra={[
          <Button
            key="refresh"
            icon={<ReloadOutlined />}
            onClick={() => refetchAllBugs()}
          >
            Refresh
          </Button>,
        ]}
      />

      <Card>
        <Space direction="vertical" style={{ width: "100%" }} size="large">
          {/* Introduction */}
          <Alert
            message="About Oracle Bug Detection"
            description={
              <Paragraph style={{ marginBottom: 0 }}>
                This database contains known Oracle bugs that can affect query
                performance and database stability. Use the tabs below to browse
                all bugs or check which bugs affect a specific Oracle version.
                Bugs are detected by analyzing execution plans, wait events, query
                characteristics, and database parameters.
              </Paragraph>
            }
            type="info"
            showIcon
          />

          {/* Tabs */}
          <Tabs defaultActiveKey="all">
            {/* All Bugs Tab */}
            <TabPane
              tab={
                <Space>
                  <BugOutlined />
                  <span>All Bugs</span>
                </Space>
              }
              key="all"
            >
              <BugList
                bugs={allBugsData?.bugs || []}
                loading={allBugsLoading}
                error={allBugsError}
                onFilterChange={handleFilterChange}
                showStats={true}
              />
            </TabPane>

            {/* Version Check Tab */}
            <TabPane
              tab={
                <Space>
                  <DatabaseOutlined />
                  <span>Check Version</span>
                </Space>
              }
              key="version"
            >
              <Space direction="vertical" style={{ width: "100%" }} size="large">
                {/* Version input */}
                <Card size="small">
                  <Space.Compact style={{ width: "100%" }}>
                    <Input
                      placeholder="Enter Oracle version (e.g., 12.1.0.1, 19c)"
                      value={versionInput}
                      onChange={(e) => setVersionInput(e.target.value)}
                      onPressEnter={handleVersionCheck}
                      prefix={<SearchOutlined />}
                    />
                    <Button
                      type="primary"
                      onClick={handleVersionCheck}
                      disabled={!versionInput.trim()}
                    >
                      Check Version
                    </Button>
                  </Space.Compact>
                </Card>

                {/* Version check results */}
                {versionToCheck && (
                  <>
                    {versionError && (
                      <Alert
                        message="Error Checking Version"
                        description={versionError.message}
                        type="error"
                        showIcon
                      />
                    )}

                    {versionData && (
                      <>
                        {/* Recommendation */}
                        <Alert
                          message="Version Analysis"
                          description={versionData.recommendation}
                          type={
                            versionData.critical_count > 0
                              ? "error"
                              : versionData.total_count > 5
                              ? "warning"
                              : versionData.total_count > 0
                              ? "info"
                              : "success"
                          }
                          showIcon
                        />

                        {/* Statistics */}
                        <Card size="small">
                          <Space split={<Divider type="vertical" />}>
                            <Text>
                              <Text strong>Total Bugs:</Text>{" "}
                              {versionData.total_count}
                            </Text>
                            <Text>
                              <Text strong style={{ color: "#cf1322" }}>
                                Critical:
                              </Text>{" "}
                              {versionData.critical_count}
                            </Text>
                            <Text>
                              <Text strong>Version:</Text>{" "}
                              {versionData.database_version}
                            </Text>
                          </Space>
                        </Card>

                        {/* Bug list */}
                        {versionData.bugs_affecting_version.length > 0 ? (
                          <BugList
                            bugs={versionData.bugs_affecting_version}
                            loading={versionLoading}
                            showStats={true}
                          />
                        ) : (
                          <Alert
                            message="No Bugs Found"
                            description={`No known bugs found for Oracle version ${versionToCheck}`}
                            type="success"
                            showIcon
                          />
                        )}
                      </>
                    )}
                  </>
                )}

                {!versionToCheck && (
                  <Alert
                    message="Enter Oracle Version"
                    description="Enter an Oracle database version above to check which bugs affect that version."
                    type="info"
                    showIcon
                  />
                )}
              </Space>
            </TabPane>
          </Tabs>
        </Space>
      </Card>
    </div>
  );
};
