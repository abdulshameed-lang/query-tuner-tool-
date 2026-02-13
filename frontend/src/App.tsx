import React, { useState, useEffect } from 'react';
import { ConfigProvider, theme, Spin } from 'antd';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { LandingPage } from './pages/LandingPage';
import { LoginPage } from './pages/LoginPage';
import { DatabaseConnectionsPage } from './pages/DatabaseConnectionsPage';
import { MainApp } from './components/MainApp';
import { authService } from './services/authService';
import './App.css';

type AppState = 'loading' | 'ready';

// Protected Route Component
const ProtectedRoute: React.FC<{ children: React.ReactElement }> = ({ children }) => {
  const isAuthenticated = authService.isAuthenticated();
  return isAuthenticated ? children : <Navigate to="/login" replace />;
};

// Login Route Component
const LoginRoute: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);

  const handleLoginSuccess = () => {
    window.location.href = '/app';
  };

  return <LoginPage onLoginSuccess={handleLoginSuccess} />;
};

// Connections Route Component
const ConnectionsRoute: React.FC = () => {
  const handleConnectionsConfigured = () => {
    window.location.href = '/app';
  };

  return <DatabaseConnectionsPage onConnectionsConfigured={handleConnectionsConfigured} />;
};

// Main App Route Component
const MainAppRoute: React.FC = () => {
  const handleLogout = () => {
    authService.logout();
    window.location.href = '/login';
  };

  const hasConnections = () => {
    const savedConnections = localStorage.getItem('database_connections');
    return savedConnections && JSON.parse(savedConnections).length > 0;
  };

  return <MainApp onLogout={handleLogout} hasConnections={hasConnections()} />;
};

const App: React.FC = () => {
  const [appState, setAppState] = useState<AppState>('loading');

  useEffect(() => {
    // Simple loading check
    setTimeout(() => setAppState('ready'), 100);
  }, []);

  if (appState === 'loading') {
    return (
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '100vh',
        }}
      >
        <Spin size="large" tip="Loading..." />
      </div>
    );
  }

  return (
    <ConfigProvider
      theme={{
        algorithm: theme.defaultAlgorithm,
        token: {
          colorPrimary: '#667eea',
        },
      }}
    >
      <Router>
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginRoute />} />
          <Route path="/connections" element={<ConnectionsRoute />} />

          {/* Protected Routes */}
          <Route
            path="/app/*"
            element={
              <ProtectedRoute>
                <MainAppRoute />
              </ProtectedRoute>
            }
          />

          {/* Redirect unknown routes to landing */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </ConfigProvider>
  );
};

export default App;
