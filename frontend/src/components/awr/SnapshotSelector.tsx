/**
 * Snapshot selector component for selecting AWR snapshot ranges
 */

import React, { useState } from "react";
import { Card, Select, Button, Space, Descriptions, Alert } from "antd";
import { ReloadOutlined } from "@ant-design/icons";
import { useAWRSnapshots } from "../../api/awrAsh";
import type { AWRSnapshot } from "../../types/awrAsh";

const { Option } = Select;

interface SnapshotSelectorProps {
  onSnapshotsSelected: (beginSnapId: number, endSnapId: number) => void;
  daysBack?: number;
}

export const SnapshotSelector: React.FC<SnapshotSelectorProps> = ({
  onSnapshotsSelected,
  daysBack = 7,
}) => {
  const [beginSnapId, setBeginSnapId] = useState<number | undefined>();
  const [endSnapId, setEndSnapId] = useState<number | undefined>();

  const { data, isLoading, error, refetch } = useAWRSnapshots(daysBack);

  const handleGenerate = () => {
    if (beginSnapId && endSnapId) {
      onSnapshotsSelected(beginSnapId, endSnapId);
    }
  };

  const getSnapshotById = (snapId: number): AWRSnapshot | undefined => {
    return data?.snapshots.find((s) => s.snap_id === snapId);
  };

  const beginSnapshot = beginSnapId ? getSnapshotById(beginSnapId) : undefined;
  const endSnapshot = endSnapId ? getSnapshotById(endSnapId) : undefined;

  if (error) {
    return (
      <Card>
        <Alert
          message="Error Loading Snapshots"
          description={error.message}
          type="error"
          showIcon
        />
      </Card>
    );
  }

  return (
    <Card
      title="Select Snapshot Range"
      extra={
        <Button
          icon={<ReloadOutlined />}
          onClick={() => refetch()}
          loading={isLoading}
        >
          Refresh
        </Button>
      }
    >
      <Space direction="vertical" style={{ width: "100%" }} size="large">
        <Space size="large">
          <div>
            <div style={{ marginBottom: 8 }}>Begin Snapshot:</div>
            <Select
              style={{ width: 250 }}
              placeholder="Select begin snapshot"
              value={beginSnapId}
              onChange={setBeginSnapId}
              loading={isLoading}
              showSearch
              filterOption={(input, option) =>
                (option?.label ?? "").toLowerCase().includes(input.toLowerCase())
              }
            >
              {data?.snapshots.map((snapshot) => (
                <Option
                  key={snapshot.snap_id}
                  value={snapshot.snap_id}
                  label={`${snapshot.snap_id} - ${new Date(
                    snapshot.begin_interval_time
                  ).toLocaleString()}`}
                >
                  {snapshot.snap_id} -{" "}
                  {new Date(snapshot.begin_interval_time).toLocaleString()}
                </Option>
              ))}
            </Select>
          </div>

          <div>
            <div style={{ marginBottom: 8 }}>End Snapshot:</div>
            <Select
              style={{ width: 250 }}
              placeholder="Select end snapshot"
              value={endSnapId}
              onChange={setEndSnapId}
              loading={isLoading}
              showSearch
              disabled={!beginSnapId}
              filterOption={(input, option) =>
                (option?.label ?? "").toLowerCase().includes(input.toLowerCase())
              }
            >
              {data?.snapshots
                .filter((s) => beginSnapId ? s.snap_id > beginSnapId : true)
                .map((snapshot) => (
                  <Option
                    key={snapshot.snap_id}
                    value={snapshot.snap_id}
                    label={`${snapshot.snap_id} - ${new Date(
                      snapshot.end_interval_time
                    ).toLocaleString()}`}
                  >
                    {snapshot.snap_id} -{" "}
                    {new Date(snapshot.end_interval_time).toLocaleString()}
                  </Option>
                ))}
            </Select>
          </div>

          <Button
            type="primary"
            onClick={handleGenerate}
            disabled={!beginSnapId || !endSnapId || beginSnapId >= endSnapId}
          >
            Generate Report
          </Button>
        </Space>

        {beginSnapshot && endSnapshot && (
          <Descriptions bordered size="small" column={2}>
            <Descriptions.Item label="Begin Time">
              {new Date(beginSnapshot.begin_interval_time).toLocaleString()}
            </Descriptions.Item>
            <Descriptions.Item label="End Time">
              {new Date(endSnapshot.end_interval_time).toLocaleString()}
            </Descriptions.Item>
            <Descriptions.Item label="Elapsed Time">
              {(
                (new Date(endSnapshot.end_interval_time).getTime() -
                  new Date(beginSnapshot.begin_interval_time).getTime()) /
                1000 /
                60
              ).toFixed(2)}{" "}
              minutes
            </Descriptions.Item>
            <Descriptions.Item label="Snapshot Count">
              {endSnapId - beginSnapId + 1}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Space>
    </Card>
  );
};
