/**
 * Operation changes panel component.
 */

import React from 'react';
import { List, Tag, Card } from 'antd';
import { SignificantChange } from '../../types/planComparison';
import { getSeverityColor, getChangeTypeIcon } from '../../api/planComparison';

interface OperationChangesPanelProps {
  changes: SignificantChange[];
}

const OperationChangesPanel: React.FC<OperationChangesPanelProps> = ({ changes }) => {
  return (
    <List
      dataSource={changes}
      renderItem={(change) => (
        <Card size="small" style={{ marginBottom: 8 }}>
          <List.Item>
            <List.Item.Meta
              avatar={<span style={{ fontSize: 24 }}>{getChangeTypeIcon(change.type)}</span>}
              title={
                <span>
                  <Tag color={getSeverityColor(change.severity)}>{change.severity.toUpperCase()}</Tag>
                  {change.message}
                </span>
              }
              description={
                <div style={{ marginTop: 8 }}>
                  {change.object_name && <div><strong>Object:</strong> {change.object_name}</div>}
                  {change.historical_method && change.current_method && (
                    <div>
                      <strong>Access Method Change:</strong>{' '}
                      <Tag>{change.historical_method}</Tag> → <Tag>{change.current_method}</Tag>
                    </div>
                  )}
                  {change.historical_sequence && change.current_sequence && (
                    <div>
                      <strong>Join Order Changed</strong>
                      <div>Historical: {change.historical_sequence.join(' → ')}</div>
                      <div>Current: {change.current_sequence.join(' → ')}</div>
                    </div>
                  )}
                </div>
              }
            />
          </List.Item>
        </Card>
      )}
    />
  );
};

export default OperationChangesPanel;
