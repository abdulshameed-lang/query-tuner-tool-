/**
 * Plan diff panel component.
 */

import React from 'react';
import { Card, Descriptions, Tag, List, Empty, Collapse } from 'antd';
import { PlusOutlined, MinusOutlined, EditOutlined } from '@ant-design/icons';
import { PlanDiff } from '../../types/planComparison';

interface PlanDiffPanelProps {
  diff: PlanDiff;
}

const PlanDiffPanel: React.FC<PlanDiffPanelProps> = ({ diff }) => {
  return (
    <div>
      <Descriptions bordered size="small" column={3} style={{ marginBottom: 16 }}>
        <Descriptions.Item label="Operations Added">
          <Tag color="green" icon={<PlusOutlined />}>{diff.operations_added}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="Operations Removed">
          <Tag color="red" icon={<MinusOutlined />}>{diff.operations_removed}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="Operations Modified">
          <Tag color="orange" icon={<EditOutlined />}>{diff.operations_modified}</Tag>
        </Descriptions.Item>
      </Descriptions>

      <Collapse defaultActiveKey={[]}>
        {diff.added_details.length > 0 && (
          <Collapse.Panel header={`Added Operations (${diff.added_details.length})`} key="added">
            <List
              dataSource={diff.added_details}
              renderItem={(op: any) => (
                <List.Item>
                  <Tag color="green">NEW</Tag>
                  {op.operation} {op.options} - {op.object_name || 'N/A'}
                </List.Item>
              )}
            />
          </Collapse.Panel>
        )}

        {diff.removed_details.length > 0 && (
          <Collapse.Panel header={`Removed Operations (${diff.removed_details.length})`} key="removed">
            <List
              dataSource={diff.removed_details}
              renderItem={(op: any) => (
                <List.Item>
                  <Tag color="red">REMOVED</Tag>
                  {op.operation} {op.options} - {op.object_name || 'N/A'}
                </List.Item>
              )}
            />
          </Collapse.Panel>
        )}

        {diff.modified_details.length > 0 && (
          <Collapse.Panel header={`Modified Operations (${diff.modified_details.length})`} key="modified">
            <List
              dataSource={diff.modified_details}
              renderItem={(change) => (
                <List.Item>
                  <List.Item.Meta
                    title={<><Tag color="orange">MODIFIED</Tag> {change.signature}</>}
                    description={
                      change.changes && change.changes.length > 0 ? (
                        <ul style={{ marginTop: 8, paddingLeft: 20 }}>
                          {change.changes.map((c, idx) => (
                            <li key={idx}>{c}</li>
                          ))}
                        </ul>
                      ) : 'No details available'
                    }
                  />
                </List.Item>
              )}
            />
          </Collapse.Panel>
        )}
      </Collapse>

      {diff.total_changes === 0 && <Empty description="No plan differences detected" />}
    </div>
  );
};

export default PlanDiffPanel;
