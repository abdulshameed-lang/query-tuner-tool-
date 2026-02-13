import React, { useState, useEffect } from 'react';
import { Layout, Menu, Button, Typography, Dropdown, Card, Tag, Space } from 'antd';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import {
  LogoutOutlined,
  UserOutlined,
  DatabaseOutlined,
  DashboardOutlined,
  ThunderboltOutlined,
  BarChartOutlined,
  BugOutlined,
  SettingOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import type { MenuProps } from 'antd';
import {
  DatabaseType,
  DatabaseConnection,
  DATABASE_LABELS,
  DATABASE_ICONS,
  DATABASE_FEATURES,
} from '../types/database';
import { QueriesListPage } from '../pages/QueriesListPage';
import { QueryDetailPage } from '../pages/QueryDetailPage';
import { WaitEventsPage } from '../pages/WaitEventsPage';
import { BugDetectionPage } from '../pages/BugDetectionPage';
import { PerformanceReportsPage } from '../pages/PerformanceReportsPage';
import { DeadlocksPage } from '../pages/DeadlocksPage';

const { Header, Content, Sider } = Layout;
const { Title, Text } = Typography;

interface MainAppProps {
  onLogout: () => void;
  hasConnections: boolean;
}

const DashboardHome: React.FC<{ connection: DatabaseConnection | null }> = ({ connection }) => {
  const navigate = useNavigate();

  if (!connection) return null;

  const features = DATABASE_FEATURES[connection.database_type];

  const featureCards = [
    {
      key: 'queries',
      title: 'Query Tuning',
      description: 'Analyze slow queries and get optimization recommendations',
      enabled: features.supportsQueryTuning,
      icon: <ThunderboltOutlined style={{ fontSize: 32, color: '#1890ff' }} />,
      path: '/queries',
    },
    {
      key: 'execution-plans',
      title: 'Execution Plans',
      description: 'Visual execution plan analysis with cost breakdown',
      enabled: features.supportsExecutionPlans,
      icon: <BarChartOutlined style={{ fontSize: 32, color: '#52c41a' }} />,
      path: '/execution-plans',
    },
    {
      key: 'wait-events',
      title: 'Wait Events',
      description: 'Monitor wait events and identify bottlenecks',
      enabled: features.supportsWaitEvents,
      icon: <DashboardOutlined style={{ fontSize: 32, color: '#fa8c16' }} />,
      path: '/wait-events',
    },
    {
      key: 'bugs',
      title: 'Bug Detection',
      description: 'Detect known database bugs and get workarounds',
      enabled: features.supportsBugDetection,
      icon: <BugOutlined style={{ fontSize: 32, color: '#f5222d' }} />,
      path: '/bugs',
    },
    {
      key: 'performance',
      title: 'Performance Reports',
      description: features.supportsAWR ? 'AWR/ASH reports and historical analysis' : 'Performance monitoring and reports',
      enabled: features.supportsAWR || features.supportsQueryTuning,
      icon: <BarChartOutlined style={{ fontSize: 32, color: '#722ed1' }} />,
      path: '/performance',
    },
    {
      key: 'deadlocks',
      title: 'Deadlock Detection',
      description: 'Identify and visualize database deadlocks',
      enabled: features.supportsDeadlockDetection,
      icon: <DatabaseOutlined style={{ fontSize: 32, color: '#eb2f96' }} />,
      path: '/deadlocks',
    },
  ];

  return (
    <div>
      <Title level={2}>
        <DashboardOutlined /> Dashboard
      </Title>
      <Text>
        Welcome to the Query Tuner dashboard! Your database connection is configured and ready.
        Select a feature below to start analyzing and tuning your database performance.
      </Text>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        gap: '16px',
        marginTop: '24px',
      }}>
        {featureCards.map((feature) => (
          <Card
            key={feature.key}
            hoverable={feature.enabled}
            onClick={() => feature.enabled && navigate(feature.path)}
            style={{
              opacity: feature.enabled ? 1 : 0.5,
              cursor: feature.enabled ? 'pointer' : 'not-allowed',
            }}
          >
            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                {feature.icon}
                {feature.enabled ? (
                  <Tag color="success">Available</Tag>
                ) : (
                  <Tag>Not Supported</Tag>
                )}
              </div>
              <div>
                <Title level={4} style={{ marginBottom: 8 }}>{feature.title}</Title>
                <Text type="secondary">{feature.description}</Text>
              </div>
            </Space>
          </Card>
        ))}
      </div>
    </div>
  );
};

const MainAppContent: React.FC<MainAppProps> = ({ onLogout }) => {
  const [connections, setConnections] = useState<DatabaseConnection[]>([]);
  const [selectedConnection, setSelectedConnection] = useState<DatabaseConnection | null>(null);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const savedConnections = localStorage.getItem('database_connections');
    if (savedConnections) {
      const parsed = JSON.parse(savedConnections);
      setConnections(parsed);
      const defaultConn = parsed.find((c: DatabaseConnection) => c.is_default) || parsed[0];
      setSelectedConnection(defaultConn);
    }
  }, []);

  const userMenuItems: MenuProps['items'] = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: 'Profile',
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: 'Settings',
    },
    {
      key: 'divider',
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Logout',
      onClick: onLogout,
    },
  ];

  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: 'Dashboard',
      onClick: () => navigate('/'),
    },
    {
      key: '/queries',
      icon: <ThunderboltOutlined />,
      label: 'Query Analysis',
      onClick: () => navigate('/queries'),
    },
    {
      key: '/performance',
      icon: <BarChartOutlined />,
      label: 'Performance Reports',
      onClick: () => navigate('/performance'),
    },
    {
      key: '/bugs',
      icon: <BugOutlined />,
      label: 'Bug Detection',
      onClick: () => navigate('/bugs'),
    },
    {
      key: '/deadlocks',
      icon: <WarningOutlined />,
      label: 'Deadlock Detection',
      onClick: () => navigate('/deadlocks'),
    },
    {
      key: '/connections',
      icon: <DatabaseOutlined />,
      label: 'Manage Connections',
      onClick: () => navigate('/connections'),
    },
  ];

  const selectedKey = location.pathname;

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: '#001529',
        padding: '0 50px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <DatabaseOutlined style={{ fontSize: '24px', color: '#fff', marginRight: '16px' }} />
          <Title level={3} style={{ color: '#fff', margin: 0 }}>
            Query Tuner
          </Title>
        </div>
        <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
          <Button
            type="text"
            icon={<UserOutlined />}
            style={{ color: '#fff' }}
          >
            Account
          </Button>
        </Dropdown>
      </Header>

      <Layout>
        <Sider width={250} style={{ background: '#fff' }}>
          <Menu
            mode="inline"
            selectedKeys={[selectedKey]}
            style={{ height: '100%', borderRight: 0 }}
            items={menuItems}
          />
        </Sider>

        <Content style={{ padding: '40px', background: '#f0f2f5' }}>
          {selectedConnection && (
            <Card style={{ marginBottom: '24px', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Space size="large">
                  <span style={{ fontSize: 48 }}>
                    {DATABASE_ICONS[selectedConnection.database_type]}
                  </span>
                  <div>
                    <Title level={3} style={{ margin: 0, color: '#fff' }}>
                      {selectedConnection.connection_name}
                    </Title>
                    <Text style={{ color: 'rgba(255,255,255,0.85)', fontSize: 16 }}>
                      {DATABASE_LABELS[selectedConnection.database_type]} •{' '}
                      {selectedConnection.host}:{selectedConnection.port}
                    </Text>
                  </div>
                </Space>
                {selectedConnection.is_default && (
                  <Tag color="gold" style={{ fontSize: 14, padding: '4px 12px' }}>
                    Default Connection
                  </Tag>
                )}
              </div>
            </Card>
          )}

          <Card>
            <Routes>
              <Route path="/" element={<DashboardHome connection={selectedConnection} />} />
              <Route path="/queries" element={<QueriesListPage />} />
              <Route path="/queries/:sqlId" element={<QueryDetailPage />} />
              <Route path="/wait-events" element={<WaitEventsPage />} />
              <Route path="/bugs" element={<BugDetectionPage />} />
              <Route path="/performance" element={<PerformanceReportsPage />} />
              <Route path="/deadlocks" element={<DeadlocksPage />} />
              <Route path="/connections" element={<div>Manage Connections (Coming Soon)</div>} />
            </Routes>
          </Card>
        </Content>
      </Layout>
    </Layout>
  );
};

export const MainApp: React.FC<MainAppProps> = (props) => {
  return <MainAppContent {...props} />;
};
