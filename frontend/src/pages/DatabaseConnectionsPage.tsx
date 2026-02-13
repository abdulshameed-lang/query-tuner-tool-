import React, { useState } from 'react';
import {
  Card,
  Button,
  List,
  Tag,
  Space,
  Modal,
  Form,
  Input,
  Select,
  InputNumber,
  Switch,
  message,
  Empty,
  Divider,
  Typography,
  Row,
  Col,
  Badge,
} from 'antd';
import {
  PlusOutlined,
  DatabaseOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  EditOutlined,
  DeleteOutlined,
  ApiOutlined,
} from '@ant-design/icons';
import {
  DatabaseType,
  DatabaseConnection,
  DATABASE_LABELS,
  DATABASE_ICONS,
  DATABASE_DEFAULT_PORTS,
  DATABASE_FEATURES,
} from '../types/database';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;
const { Option } = Select;

interface DatabaseConnectionsPageProps {
  onConnectionsConfigured: () => void;
}

export const DatabaseConnectionsPage: React.FC<DatabaseConnectionsPageProps> = ({
  onConnectionsConfigured,
}) => {
  const [connections, setConnections] = useState<DatabaseConnection[]>(() => {
    const saved = localStorage.getItem('database_connections');
    return saved ? JSON.parse(saved) : [];
  });
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingConnection, setEditingConnection] = useState<DatabaseConnection | null>(null);
  const [testingConnection, setTestingConnection] = useState(false);
  const [form] = Form.useForm();
  const [selectedDbType, setSelectedDbType] = useState<DatabaseType>(DatabaseType.ORACLE);

  const handleAddConnection = () => {
    setEditingConnection(null);
    form.resetFields();
    form.setFieldsValue({
      database_type: DatabaseType.ORACLE,
      port: DATABASE_DEFAULT_PORTS[DatabaseType.ORACLE],
      is_default: connections.length === 0,
      ssl_enabled: false,
    });
    setIsModalVisible(true);
  };

  const handleEditConnection = (connection: DatabaseConnection) => {
    setEditingConnection(connection);
    form.setFieldsValue(connection);
    setSelectedDbType(connection.database_type);
    setIsModalVisible(true);
  };

  const handleDeleteConnection = (id: number) => {
    Modal.confirm({
      title: 'Delete Connection',
      content: 'Are you sure you want to delete this connection?',
      okText: 'Delete',
      okType: 'danger',
      onOk: () => {
        const updatedConnections = connections.filter((c) => c.id !== id);
        setConnections(updatedConnections);
        localStorage.setItem('database_connections', JSON.stringify(updatedConnections));
        message.success('Connection deleted successfully');
      },
    });
  };

  const handleTestConnection = async () => {
    try {
      await form.validateFields();
      setTestingConnection(true);

      // Simulate connection test
      setTimeout(() => {
        setTestingConnection(false);
        message.success('Connection test successful!');
      }, 1500);
    } catch (error) {
      message.error('Please fill in all required fields');
    }
  };

  const handleSaveConnection = async () => {
    try {
      const values = await form.validateFields();
      const newConnection: DatabaseConnection = {
        ...values,
        id: editingConnection?.id || Date.now(),
        created_at: editingConnection?.created_at || new Date().toISOString(),
        is_active: true,
      };

      let updatedConnections;
      if (editingConnection) {
        updatedConnections = connections.map((c) =>
          c.id === editingConnection.id ? newConnection : c
        );
        message.success('Connection updated successfully');
      } else {
        updatedConnections = [...connections, newConnection];
        message.success('Connection added successfully');
      }

      setConnections(updatedConnections);
      localStorage.setItem('database_connections', JSON.stringify(updatedConnections));

      setIsModalVisible(false);
      form.resetFields();
    } catch (error) {
      console.error('Validation failed:', error);
    }
  };

  const handleDbTypeChange = (type: DatabaseType) => {
    setSelectedDbType(type);
    form.setFieldsValue({
      port: DATABASE_DEFAULT_PORTS[type],
    });
  };

  const renderConnectionForm = () => {
    const features = DATABASE_FEATURES[selectedDbType];

    return (
      <Form form={form} layout="vertical" size="large">
        <Form.Item
          name="connection_name"
          label="Connection Name"
          rules={[{ required: true, message: 'Please enter a connection name' }]}
        >
          <Input placeholder="My Production Database" />
        </Form.Item>

        <Form.Item
          name="database_type"
          label="Database Type"
          rules={[{ required: true }]}
        >
          <Select onChange={handleDbTypeChange} size="large">
            {Object.entries(DATABASE_LABELS).map(([key, label]) => (
              <Option key={key} value={key}>
                <Space>
                  <span>{DATABASE_ICONS[key as DatabaseType]}</span>
                  <span>{label}</span>
                </Space>
              </Option>
            ))}
          </Select>
        </Form.Item>

        <Row gutter={16}>
          <Col span={16}>
            <Form.Item
              name="host"
              label="Host"
              rules={[{ required: true, message: 'Please enter host' }]}
            >
              <Input placeholder="localhost or 192.168.1.100" />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item
              name="port"
              label="Port"
              rules={[{ required: true, message: 'Please enter port' }]}
            >
              <InputNumber style={{ width: '100%' }} min={1} max={65535} />
            </Form.Item>
          </Col>
        </Row>

        {/* Oracle-specific fields */}
        {selectedDbType === DatabaseType.ORACLE && (
          <>
            <Form.Item
              name="service_name"
              label="Service Name"
              tooltip="Either Service Name or SID is required"
            >
              <Input placeholder="ORCLPDB" />
            </Form.Item>

            <Form.Item name="sid" label="SID (alternative to Service Name)">
              <Input placeholder="ORCL" />
            </Form.Item>
          </>
        )}

        {/* PostgreSQL/MySQL/SQL Server - Database Name */}
        {(selectedDbType === DatabaseType.POSTGRESQL ||
          selectedDbType === DatabaseType.MYSQL ||
          selectedDbType === DatabaseType.SQLSERVER) && (
          <Form.Item
            name="database_name"
            label="Database Name"
            rules={[{ required: true, message: 'Please enter database name' }]}
          >
            <Input placeholder="mydb" />
          </Form.Item>
        )}

        {/* MongoDB - Database Name */}
        {selectedDbType === DatabaseType.MONGODB && (
          <>
            <Form.Item name="database_name" label="Database Name">
              <Input placeholder="admin" />
            </Form.Item>

            <Form.Item name="connection_string" label="Connection String (Optional)">
              <TextArea
                placeholder="mongodb://username:password@host:port/database?authSource=admin"
                rows={2}
              />
            </Form.Item>
          </>
        )}

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="username"
              label="Username"
              rules={[{ required: true, message: 'Please enter username' }]}
            >
              <Input placeholder="admin" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="password"
              label="Password"
              rules={[{ required: true, message: 'Please enter password' }]}
            >
              <Input.Password placeholder="••••••••" />
            </Form.Item>
          </Col>
        </Row>

        <Form.Item name="ssl_enabled" label="SSL/TLS Enabled" valuePropName="checked">
          <Switch />
        </Form.Item>

        <Form.Item name="description" label="Description">
          <TextArea rows={2} placeholder="Production database for sales application" />
        </Form.Item>

        <Form.Item name="is_default" label="Set as Default Connection" valuePropName="checked">
          <Switch />
        </Form.Item>

        <Divider />

        <Card size="small" style={{ background: '#f6ffed', borderColor: '#b7eb8f' }}>
          <Title level={5} style={{ marginTop: 0 }}>
            Available Features for {DATABASE_LABELS[selectedDbType]}:
          </Title>
          <Space direction="vertical" size="small">
            {features.supportsQueryTuning && (
              <Text>
                <CheckCircleOutlined style={{ color: '#52c41a' }} /> Query Tuning & Recommendations
              </Text>
            )}
            {features.supportsExecutionPlans && (
              <Text>
                <CheckCircleOutlined style={{ color: '#52c41a' }} /> Execution Plan Analysis
              </Text>
            )}
            {features.supportsWaitEvents && (
              <Text>
                <CheckCircleOutlined style={{ color: '#52c41a' }} /> Wait Event Monitoring
              </Text>
            )}
            {features.supportsBugDetection && (
              <Text>
                <CheckCircleOutlined style={{ color: '#52c41a' }} /> Bug Detection
              </Text>
            )}
            {features.supportsAWR && (
              <Text>
                <CheckCircleOutlined style={{ color: '#52c41a' }} /> AWR/Performance Reports
              </Text>
            )}
            {features.supportsDeadlockDetection && (
              <Text>
                <CheckCircleOutlined style={{ color: '#52c41a' }} /> Deadlock Detection
              </Text>
            )}
          </Space>
        </Card>
      </Form>
    );
  };

  return (
    <div style={{ padding: '40px', minHeight: '100vh', background: '#f0f2f5' }}>
      <Card>
        <div style={{ marginBottom: 24 }}>
          <Title level={2}>
            <DatabaseOutlined /> Database Connections
          </Title>
          <Paragraph type="secondary">
            Connect to your databases to start monitoring and tuning performance. Supports Oracle,
            PostgreSQL, SQL Server, MySQL, MongoDB, and more.
          </Paragraph>
        </div>

        <Button
          type="primary"
          icon={<PlusOutlined />}
          size="large"
          onClick={handleAddConnection}
          style={{ marginBottom: 24 }}
        >
          Add Database Connection
        </Button>

        {connections.length === 0 ? (
          <Empty
            description="No database connections configured"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          >
            <Button type="primary" onClick={handleAddConnection}>
              Add Your First Database
            </Button>
          </Empty>
        ) : (
          <>
            <List
              dataSource={connections}
              renderItem={(connection) => (
                <List.Item
                  actions={[
                    <Button
                      icon={<EditOutlined />}
                      onClick={() => handleEditConnection(connection)}
                    >
                      Edit
                    </Button>,
                    <Button
                      danger
                      icon={<DeleteOutlined />}
                      onClick={() => handleDeleteConnection(connection.id!)}
                    >
                      Delete
                    </Button>,
                  ]}
                >
                  <List.Item.Meta
                    avatar={
                      <div style={{ fontSize: 40 }}>
                        {DATABASE_ICONS[connection.database_type]}
                      </div>
                    }
                    title={
                      <Space>
                        {connection.connection_name}
                        {connection.is_default && <Tag color="blue">Default</Tag>}
                        <Badge status={connection.is_active ? 'success' : 'default'} />
                      </Space>
                    }
                    description={
                      <Space direction="vertical" size="small">
                        <Text type="secondary">
                          {DATABASE_LABELS[connection.database_type]} •{' '}
                          {connection.username}@{connection.host}:{connection.port}
                        </Text>
                        {connection.description && <Text type="secondary">{connection.description}</Text>}
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />

            <Divider />

            <div style={{ textAlign: 'center' }}>
              <Button
                type="primary"
                size="large"
                icon={<ApiOutlined />}
                onClick={onConnectionsConfigured}
              >
                Continue to Dashboard
              </Button>
            </div>
          </>
        )}
      </Card>

      <Modal
        title={editingConnection ? 'Edit Connection' : 'Add New Database Connection'}
        open={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        width={700}
        footer={[
          <Button key="test" loading={testingConnection} onClick={handleTestConnection}>
            Test Connection
          </Button>,
          <Button key="cancel" onClick={() => setIsModalVisible(false)}>
            Cancel
          </Button>,
          <Button key="save" type="primary" onClick={handleSaveConnection}>
            {editingConnection ? 'Update' : 'Save'} Connection
          </Button>,
        ]}
      >
        {renderConnectionForm()}
      </Modal>
    </div>
  );
};
