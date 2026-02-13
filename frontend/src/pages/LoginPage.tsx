import React, { useState } from 'react';
import { Form, Input, Button, Card, Typography, Alert, Space } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons';
import { authService } from '../services/authService';
import './AuthPages.css';

const { Title, Text } = Typography;

interface LoginPageProps {
  onLoginSuccess: () => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSignup, setIsSignup] = useState(false);
  const [loginForm] = Form.useForm();
  const [signupForm] = Form.useForm();

  console.log('LoginPage rendered, isSignup:', isSignup);

  const handleLogin = async (values: any) => {
    console.log('handleLogin called with:', values);
    setLoading(true);
    setError(null);

    try {
      const response = await authService.login({
        username: values.username,
        password: values.password,
      });
      console.log('Login successful:', response.user);
      onLoginSuccess();
    } catch (err: any) {
      console.error('Login error:', err);
      const errorMessage = err.response?.data?.detail || 'Login failed. Please try again.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleSignup = async (values: any) => {
    console.log('handleSignup called with:', values);
    setLoading(true);
    setError(null);

    try {
      const response = await authService.signup({
        username: values.username,
        email: values.email,
        password: values.password,
        full_name: values.full_name,
      });
      console.log('Signup successful:', response.user);
      onLoginSuccess();
    } catch (err: any) {
      console.error('Signup error:', err);
      const errorMessage = err.response?.data?.detail || 'Signup failed. Please try again.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleSignup = () => {
    console.log('Toggle signup clicked, current isSignup:', isSignup);
    setIsSignup(true);
    setError(null);
  };

  const handleToggleLogin = () => {
    console.log('Toggle login clicked, current isSignup:', isSignup);
    setIsSignup(false);
    setError(null);
  };

  return (
    <div className="auth-container">
      <div className="auth-background"></div>
      <div className="auth-overlay">
        <div className="auth-content">
          <Card className="auth-card">
            <div className="auth-header">
              <Title level={2}>Oracle Query Tuner</Title>
              <Text type="secondary">Database Performance Analysis & Tuning Tool</Text>
            </div>

            {error && (
              <Alert
                message="Error"
                description={error}
                type="error"
                closable
                onClose={() => setError(null)}
                style={{ marginBottom: 24 }}
              />
            )}

            <div style={{ marginBottom: 24, textAlign: 'center' }}>
              <Space size="large">
                <Button
                  type={!isSignup ? 'primary' : 'default'}
                  size="large"
                  onClick={handleToggleLogin}
                  style={{ minWidth: 120, cursor: 'pointer' }}
                >
                  Login
                </Button>
                <Button
                  type={isSignup ? 'primary' : 'default'}
                  size="large"
                  onClick={handleToggleSignup}
                  style={{ minWidth: 120, cursor: 'pointer' }}
                >
                  Sign Up
                </Button>
              </Space>
            </div>

            {!isSignup ? (
              <div>
                <Title level={4} style={{ textAlign: 'center', color: '#52c41a' }}>
                  LOGIN FORM
                </Title>
                <Form
                  form={loginForm}
                  name="login"
                  onFinish={handleLogin}
                  layout="vertical"
                  size="large"
                >
                  <Form.Item
                    name="username"
                    rules={[{ required: true, message: 'Please enter your username' }]}
                  >
                    <Input
                      prefix={<UserOutlined />}
                      placeholder="Username"
                    />
                  </Form.Item>

                  <Form.Item
                    name="password"
                    rules={[{ required: true, message: 'Please enter your password' }]}
                  >
                    <Input.Password
                      prefix={<LockOutlined />}
                      placeholder="Password"
                    />
                  </Form.Item>

                  <Form.Item>
                    <Button
                      type="primary"
                      htmlType="submit"
                      loading={loading}
                      block
                      size="large"
                      style={{ cursor: 'pointer' }}
                    >
                      Log In
                    </Button>
                  </Form.Item>

                  <div style={{ textAlign: 'center' }}>
                    <Text type="secondary">
                      Don't have an account?{' '}
                      <a onClick={handleToggleSignup} style={{ cursor: 'pointer' }}>
                        Sign up
                      </a>
                    </Text>
                  </div>
                </Form>
              </div>
            ) : (
              <div>
                <Title level={4} style={{ textAlign: 'center', color: '#1890ff' }}>
                  SIGNUP FORM
                </Title>
                <Form
                  form={signupForm}
                  name="signup"
                  onFinish={handleSignup}
                  layout="vertical"
                  size="large"
                >
                  <Form.Item
                    name="username"
                    rules={[
                      { required: true, message: 'Please enter a username' },
                      { min: 3, message: 'Username must be at least 3 characters' }
                    ]}
                  >
                    <Input
                      prefix={<UserOutlined />}
                      placeholder="Username"
                    />
                  </Form.Item>

                  <Form.Item
                    name="email"
                    rules={[
                      { required: true, message: 'Please enter your email' },
                      { type: 'email', message: 'Please enter a valid email' }
                    ]}
                  >
                    <Input
                      prefix={<MailOutlined />}
                      placeholder="Email"
                    />
                  </Form.Item>

                  <Form.Item name="full_name">
                    <Input
                      prefix={<UserOutlined />}
                      placeholder="Full Name (optional)"
                    />
                  </Form.Item>

                  <Form.Item
                    name="password"
                    rules={[
                      { required: true, message: 'Please enter a password' },
                      { min: 6, message: 'Password must be at least 6 characters' }
                    ]}
                  >
                    <Input.Password
                      prefix={<LockOutlined />}
                      placeholder="Password"
                    />
                  </Form.Item>

                  <Form.Item
                    name="confirm_password"
                    dependencies={['password']}
                    rules={[
                      { required: true, message: 'Please confirm your password' },
                      ({ getFieldValue }) => ({
                        validator(_, value) {
                          if (!value || getFieldValue('password') === value) {
                            return Promise.resolve();
                          }
                          return Promise.reject(new Error('Passwords do not match'));
                        },
                      }),
                    ]}
                  >
                    <Input.Password
                      prefix={<LockOutlined />}
                      placeholder="Confirm Password"
                    />
                  </Form.Item>

                  <Form.Item>
                    <Button
                      type="primary"
                      htmlType="submit"
                      loading={loading}
                      block
                      size="large"
                      style={{ cursor: 'pointer' }}
                      onClick={(e) => {
                        console.log('Sign Up button clicked!', e);
                      }}
                    >
                      Create Account
                    </Button>
                  </Form.Item>

                  <div style={{ textAlign: 'center' }}>
                    <Text type="secondary">
                      Already have an account?{' '}
                      <a onClick={handleToggleLogin} style={{ cursor: 'pointer' }}>
                        Log in
                      </a>
                    </Text>
                  </div>
                </Form>
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
};
