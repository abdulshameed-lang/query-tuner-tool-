import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, Row, Col, Typography, Space, Divider } from 'antd';
import {
  ThunderboltOutlined,
  BarChartOutlined,
  BugOutlined,
  DatabaseOutlined,
  CheckCircleOutlined,
  RocketOutlined,
  SafetyOutlined,
  ClockCircleOutlined,
  WarningOutlined,
  DashboardOutlined,
  LoginOutlined,
} from '@ant-design/icons';

const { Title, Paragraph, Text } = Typography;

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();

  const features = [
    {
      icon: <ThunderboltOutlined style={{ fontSize: 48, color: '#faad14' }} />,
      title: 'Query Performance Analysis',
      description: 'Identify slow queries instantly. Get real-time insights from V$SQL with elapsed time, CPU usage, and execution metrics.',
      color: '#fff7e6',
    },
    {
      icon: <BarChartOutlined style={{ fontSize: 48, color: '#1890ff' }} />,
      title: 'Execution Plan Visualization',
      description: 'Interactive execution plan trees with cost breakdown. Identify expensive operations at a glance.',
      color: '#e6f7ff',
    },
    {
      icon: <DashboardOutlined style={{ fontSize: 48, color: '#52c41a' }} />,
      title: 'Wait Events Monitoring',
      description: 'Track I/O, CPU, and concurrency bottlenecks. Real-time wait event analysis with intelligent recommendations.',
      color: '#f6ffed',
    },
    {
      icon: <BugOutlined style={{ fontSize: 48, color: '#f5222d' }} />,
      title: 'Bug Detection',
      description: 'Detect known Oracle bugs automatically. Get workarounds and remediation steps for critical issues.',
      color: '#fff1f0',
    },
    {
      icon: <ClockCircleOutlined style={{ fontSize: 48, color: '#722ed1' }} />,
      title: 'AWR/ASH Reports',
      description: 'Historical performance analysis with AWR snapshots. Generate comprehensive reports for any time range.',
      color: '#f9f0ff',
    },
    {
      icon: <WarningOutlined style={{ fontSize: 48, color: '#fa8c16' }} />,
      title: 'Deadlock Detection',
      description: 'Visualize database deadlocks with interactive graphs. Understand session dependencies and get prevention tips.',
      color: '#fff7e6',
    },
  ];

  const benefits = [
    {
      icon: <RocketOutlined style={{ fontSize: 32, color: '#1890ff' }} />,
      title: 'Boost Performance',
      description: 'Improve query response times by up to 10x with actionable tuning recommendations.',
    },
    {
      icon: <SafetyOutlined style={{ fontSize: 32, color: '#52c41a' }} />,
      title: 'Prevent Issues',
      description: 'Detect and resolve problems before they impact production systems.',
    },
    {
      icon: <CheckCircleOutlined style={{ fontSize: 32, color: '#722ed1' }} />,
      title: 'Save Time',
      description: 'Automated analysis reduces troubleshooting time from hours to minutes.',
    },
  ];

  return (
    <div style={{ minHeight: '100vh', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
      {/* Header */}
      <div
        style={{
          padding: '20px 50px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'rgba(255, 255, 255, 0.1)',
          backdropFilter: 'blur(10px)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <DatabaseOutlined style={{ fontSize: 40, color: '#fff' }} />
          <div>
            <Title level={2} style={{ color: '#fff', margin: 0, fontWeight: 700 }}>
              RARE-IT
            </Title>
            <Text style={{ color: 'rgba(255,255,255,0.85)', fontSize: 12 }}>
              QueryTune Pro
            </Text>
          </div>
        </div>
        <Button
          type="primary"
          size="large"
          icon={<LoginOutlined />}
          onClick={() => navigate('/login')}
          style={{
            background: '#fff',
            color: '#667eea',
            borderColor: '#fff',
            fontWeight: 600,
            height: 48,
            fontSize: 16,
          }}
        >
          Login to Dashboard
        </Button>
      </div>

      {/* Hero Section */}
      <div style={{ padding: '80px 50px', textAlign: 'center' }}>
        <Title
          level={1}
          style={{
            color: '#fff',
            fontSize: 56,
            fontWeight: 800,
            marginBottom: 24,
            textShadow: '0 2px 4px rgba(0,0,0,0.2)',
          }}
        >
          Oracle Database Performance Tuning
          <br />
          Made Simple
        </Title>
        <Paragraph
          style={{
            color: 'rgba(255,255,255,0.95)',
            fontSize: 20,
            maxWidth: 800,
            margin: '0 auto 40px',
            lineHeight: 1.8,
          }}
        >
          Comprehensive Oracle performance monitoring and tuning platform.
          <br />
          Identify bottlenecks, optimize queries, and prevent issues before they impact your business.
        </Paragraph>
        <Space size="large">
          <Button
            type="primary"
            size="large"
            icon={<RocketOutlined />}
            onClick={() => navigate('/login')}
            style={{
              background: '#faad14',
              borderColor: '#faad14',
              height: 56,
              fontSize: 18,
              fontWeight: 600,
              padding: '0 40px',
              boxShadow: '0 4px 12px rgba(250, 173, 20, 0.4)',
            }}
          >
            Get Started Free
          </Button>
          <Button
            size="large"
            onClick={() => document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })}
            style={{
              background: 'rgba(255,255,255,0.2)',
              borderColor: '#fff',
              color: '#fff',
              height: 56,
              fontSize: 18,
              fontWeight: 600,
              padding: '0 40px',
              backdropFilter: 'blur(10px)',
            }}
          >
            Learn More
          </Button>
        </Space>
      </div>

      {/* Features Section */}
      <div
        id="features"
        style={{
          background: '#f0f2f5',
          padding: '80px 50px',
        }}
      >
        <div style={{ maxWidth: 1400, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: 60 }}>
            <Title level={2} style={{ fontSize: 42, fontWeight: 700, marginBottom: 16 }}>
              Powerful Features for Oracle DBAs
            </Title>
            <Paragraph style={{ fontSize: 18, color: '#666', maxWidth: 700, margin: '0 auto' }}>
              Everything you need to monitor, analyze, and optimize your Oracle databases
            </Paragraph>
          </div>

          <Row gutter={[32, 32]}>
            {features.map((feature, index) => (
              <Col xs={24} md={12} lg={8} key={index}>
                <Card
                  hoverable
                  style={{
                    height: '100%',
                    borderRadius: 12,
                    border: 'none',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
                    transition: 'all 0.3s ease',
                  }}
                  bodyStyle={{ padding: 32 }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'translateY(-8px)';
                    e.currentTarget.style.boxShadow = '0 12px 24px rgba(0,0,0,0.15)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.08)';
                  }}
                >
                  <div
                    style={{
                      width: 80,
                      height: 80,
                      borderRadius: 16,
                      background: feature.color,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      marginBottom: 20,
                    }}
                  >
                    {feature.icon}
                  </div>
                  <Title level={4} style={{ marginBottom: 12, fontWeight: 600 }}>
                    {feature.title}
                  </Title>
                  <Paragraph style={{ color: '#666', fontSize: 15, lineHeight: 1.7 }}>
                    {feature.description}
                  </Paragraph>
                </Card>
              </Col>
            ))}
          </Row>
        </div>
      </div>

      {/* Benefits Section */}
      <div
        style={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          padding: '80px 50px',
        }}
      >
        <div style={{ maxWidth: 1400, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: 60 }}>
            <Title level={2} style={{ fontSize: 42, fontWeight: 700, color: '#fff', marginBottom: 16 }}>
              Why Choose RARE-IT QueryTune Pro?
            </Title>
            <Paragraph style={{ fontSize: 18, color: 'rgba(255,255,255,0.9)', maxWidth: 700, margin: '0 auto' }}>
              Trusted by DBAs worldwide to keep Oracle databases running at peak performance
            </Paragraph>
          </div>

          <Row gutter={[48, 48]}>
            {benefits.map((benefit, index) => (
              <Col xs={24} md={8} key={index}>
                <div style={{ textAlign: 'center' }}>
                  <div
                    style={{
                      width: 100,
                      height: 100,
                      borderRadius: '50%',
                      background: 'rgba(255,255,255,0.2)',
                      backdropFilter: 'blur(10px)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      margin: '0 auto 24px',
                      border: '2px solid rgba(255,255,255,0.3)',
                    }}
                  >
                    {benefit.icon}
                  </div>
                  <Title level={3} style={{ color: '#fff', marginBottom: 12, fontWeight: 600 }}>
                    {benefit.title}
                  </Title>
                  <Paragraph style={{ color: 'rgba(255,255,255,0.85)', fontSize: 16, lineHeight: 1.8 }}>
                    {benefit.description}
                  </Paragraph>
                </div>
              </Col>
            ))}
          </Row>
        </div>
      </div>

      {/* CTA Section */}
      <div style={{ background: '#fff', padding: '80px 50px', textAlign: 'center' }}>
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
          <Title level={2} style={{ fontSize: 42, fontWeight: 700, marginBottom: 24 }}>
            Ready to Optimize Your Oracle Database?
          </Title>
          <Paragraph style={{ fontSize: 18, color: '#666', marginBottom: 40 }}>
            Join hundreds of DBAs who trust RARE-IT QueryTune Pro for their Oracle performance tuning needs.
            <br />
            Start your free trial today - no credit card required.
          </Paragraph>
          <Button
            type="primary"
            size="large"
            icon={<RocketOutlined />}
            onClick={() => navigate('/login')}
            style={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              borderColor: 'transparent',
              height: 64,
              fontSize: 20,
              fontWeight: 600,
              padding: '0 48px',
              boxShadow: '0 8px 16px rgba(102, 126, 234, 0.3)',
            }}
          >
            Start Free Trial
          </Button>
        </div>
      </div>

      {/* Footer */}
      <div
        style={{
          background: '#001529',
          padding: '40px 50px',
          textAlign: 'center',
        }}
      >
        <Space direction="vertical" size="small">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12 }}>
            <DatabaseOutlined style={{ fontSize: 32, color: '#667eea' }} />
            <Title level={3} style={{ color: '#fff', margin: 0, fontWeight: 700 }}>
              RARE-IT
            </Title>
          </div>
          <Text style={{ color: 'rgba(255,255,255,0.65)' }}>
            QueryTune Pro - Professional Oracle Database Performance Tuning Platform
          </Text>
          <Divider style={{ background: 'rgba(255,255,255,0.2)', margin: '24px 0' }} />
          <Text style={{ color: 'rgba(255,255,255,0.45)', fontSize: 14 }}>
            © 2026 RARE-IT. All rights reserved. | https://rare-it.querytune.com
          </Text>
        </Space>
      </div>
    </div>
  );
};
