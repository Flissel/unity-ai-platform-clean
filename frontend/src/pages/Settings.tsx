import React, { useState, useEffect } from 'react';
import {
  CogIcon,
  ServerIcon,
  KeyIcon,
  BellIcon,
  ShieldCheckIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { useApi } from '../contexts/ApiContext';
import toast from 'react-hot-toast';

interface SystemInfo {
  version: string;
  environment: string;
  database: {
    type: string;
    migrationVersion: number;
  };
  settings: {
    timezone: string;
    userManagement: {
      disabled: boolean;
    };
  };
}

const Settings: React.FC = () => {
  const { n8nApi, playgroundApi, isConnected, checkConnection } = useApi();
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [testingConnection, setTestingConnection] = useState(false);
  const [playgroundStatus, setPlaygroundStatus] = useState<'unknown' | 'connected' | 'disconnected'>('unknown');
  
  // API Configuration
  const [apiConfig, setApiConfig] = useState({
    n8nUrl: 'https://n8n.unit-y-ai.io/api/v1',
    playgroundUrl: 'http://localhost:8000',
    timeout: 30000,
  });

  useEffect(() => {
    if (isConnected) {
      fetchSystemInfo();
    }
    checkPlaygroundConnection();
  }, [isConnected]);

  const fetchSystemInfo = async () => {
    try {
      setLoading(true);
      const response = await n8nApi.get('/settings');
      setSystemInfo(response.data);
    } catch (error) {
      console.error('Failed to fetch system info:', error);
      toast.error('Failed to load system information');
    } finally {
      setLoading(false);
    }
  };

  const checkPlaygroundConnection = async () => {
    try {
      await playgroundApi.get('/health');
      setPlaygroundStatus('connected');
    } catch (error) {
      setPlaygroundStatus('disconnected');
    }
  };

  const testN8nConnection = async () => {
    setTestingConnection(true);
    try {
      await checkConnection();
      toast.success('n8n API connection successful');
    } catch (error) {
      toast.error('n8n API connection failed');
    } finally {
      setTestingConnection(false);
    }
  };

  const testPlaygroundConnection = async () => {
    setTestingConnection(true);
    try {
      await checkPlaygroundConnection();
      if (playgroundStatus === 'connected') {
        toast.success('Playground API connection successful');
      } else {
        toast.error('Playground API connection failed');
      }
    } catch (error) {
      toast.error('Playground API connection failed');
    } finally {
      setTestingConnection(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connected':
        return <CheckCircleIcon className="h-5 w-5 text-success-500" />;
      case 'disconnected':
        return <XCircleIcon className="h-5 w-5 text-error-500" />;
      default:
        return <ExclamationTriangleIcon className="h-5 w-5 text-warning-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'connected':
        return 'badge badge-success';
      case 'disconnected':
        return 'badge badge-error';
      default:
        return 'badge badge-warning';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
            Settings
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Configure your n8n environment and API connections
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* API Connections */}
        <div className="bg-white shadow-sm rounded-lg border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900 flex items-center">
              <ServerIcon className="h-5 w-5 mr-2" />
              API Connections
            </h3>
          </div>
          <div className="px-6 py-4 space-y-4">
            {/* n8n API */}
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                {getStatusIcon(isConnected ? 'connected' : 'disconnected')}
                <div>
                  <p className="text-sm font-medium text-gray-900">n8n API</p>
                  <p className="text-sm text-gray-500">{apiConfig.n8nUrl}</p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <span className={getStatusBadge(isConnected ? 'connected' : 'disconnected')}>
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
                <button
                  onClick={testN8nConnection}
                  disabled={testingConnection}
                  className="btn-outline btn-sm"
                >
                  Test
                </button>
              </div>
            </div>

            {/* Playground API */}
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                {getStatusIcon(playgroundStatus)}
                <div>
                  <p className="text-sm font-medium text-gray-900">Playground API</p>
                  <p className="text-sm text-gray-500">{apiConfig.playgroundUrl}</p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <span className={getStatusBadge(playgroundStatus)}>
                  {playgroundStatus === 'connected' ? 'Connected' : 
                   playgroundStatus === 'disconnected' ? 'Disconnected' : 'Unknown'}
                </span>
                <button
                  onClick={testPlaygroundConnection}
                  disabled={testingConnection}
                  className="btn-outline btn-sm"
                >
                  Test
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* System Information */}
        <div className="bg-white shadow-sm rounded-lg border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900 flex items-center">
              <CogIcon className="h-5 w-5 mr-2" />
              System Information
            </h3>
          </div>
          <div className="px-6 py-4">
            {loading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600 mx-auto"></div>
                <p className="mt-2 text-sm text-gray-500">Loading system info...</p>
              </div>
            ) : systemInfo ? (
              <dl className="space-y-3">
                <div>
                  <dt className="text-sm font-medium text-gray-500">Version</dt>
                  <dd className="text-sm text-gray-900">{systemInfo.version}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Environment</dt>
                  <dd className="text-sm text-gray-900">{systemInfo.environment}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Database</dt>
                  <dd className="text-sm text-gray-900">
                    {systemInfo.database.type} (Migration: {systemInfo.database.migrationVersion})
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Timezone</dt>
                  <dd className="text-sm text-gray-900">{systemInfo.settings.timezone}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">User Management</dt>
                  <dd className="text-sm text-gray-900">
                    {systemInfo.settings.userManagement.disabled ? 'Disabled' : 'Enabled'}
                  </dd>
                </div>
              </dl>
            ) : (
              <p className="text-sm text-gray-500">Unable to load system information</p>
            )}
          </div>
        </div>

        {/* API Configuration */}
        <div className="bg-white shadow-sm rounded-lg border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900 flex items-center">
              <KeyIcon className="h-5 w-5 mr-2" />
              API Configuration
            </h3>
          </div>
          <div className="px-6 py-4 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                n8n API URL
              </label>
              <input
                type="url"
                className="input"
                value={apiConfig.n8nUrl}
                onChange={(e) => setApiConfig({...apiConfig, n8nUrl: e.target.value})}
                placeholder="https://n8n.unit-y-ai.io/api/v1"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Playground API URL
              </label>
              <input
                type="url"
                className="input"
                value={apiConfig.playgroundUrl}
                onChange={(e) => setApiConfig({...apiConfig, playgroundUrl: e.target.value})}
                placeholder="http://localhost:8000"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Request Timeout (ms)
              </label>
              <input
                type="number"
                className="input"
                value={apiConfig.timeout}
                onChange={(e) => setApiConfig({...apiConfig, timeout: parseInt(e.target.value)})}
                min="1000"
                max="120000"
              />
            </div>
            <button
              onClick={() => toast.success('Configuration saved (demo)')}
              className="btn-primary w-full"
            >
              Save Configuration
            </button>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white shadow-sm rounded-lg border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900 flex items-center">
              <BellIcon className="h-5 w-5 mr-2" />
              Quick Actions
            </h3>
          </div>
          <div className="px-6 py-4 space-y-3">
            <a
              href="https://n8n.unit-y-ai.io"
              target="_blank"
              rel="noopener noreferrer"
              className="block w-full btn-outline text-center"
            >
              Open n8n Editor
            </a>
            <a
              href="https://n8n.unit-y-ai.io/api/v1/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="block w-full btn-outline text-center"
            >
              View API Documentation
            </a>
            <button
              onClick={() => {
                fetchSystemInfo();
                checkPlaygroundConnection();
                toast.success('Status refreshed');
              }}
              className="w-full btn-outline"
            >
              Refresh All Status
            </button>
          </div>
        </div>
      </div>

      {/* Security Notice */}
      <div className="bg-primary-50 border border-primary-200 rounded-lg p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <ShieldCheckIcon className="h-5 w-5 text-primary-400" />
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-primary-800">
              Security Information
            </h3>
            <div className="mt-2 text-sm text-primary-700">
              <p>
                This interface provides read-only access to your n8n instance. 
                For security reasons, sensitive operations like credential management 
                should be performed directly in the n8n interface.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;