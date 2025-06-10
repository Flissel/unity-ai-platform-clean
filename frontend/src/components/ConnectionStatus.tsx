import React from 'react';
import { useApi } from '../contexts/ApiContext';
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';

const ConnectionStatus: React.FC = () => {
  const { isConnected, isLoading, checkConnection } = useApi();

  if (isLoading) {
    return (
      <div className="flex items-center space-x-2 text-sm text-gray-500">
        <ArrowPathIcon className="h-4 w-4 animate-spin" />
        <span>Connecting...</span>
      </div>
    );
  }

  return (
    <div className="w-full">
      <div className={`flex items-center space-x-2 text-sm ${
        isConnected ? 'text-success-600' : 'text-error-600'
      }`}>
        {isConnected ? (
          <CheckCircleIcon className="h-4 w-4" />
        ) : (
          <ExclamationTriangleIcon className="h-4 w-4" />
        )}
        <span className="font-medium">
          {isConnected ? 'Connected' : 'Disconnected'}
        </span>
      </div>
      <div className="text-xs text-gray-500 mt-1">
        n8n API: {isConnected ? 'Online' : 'Offline'}
      </div>
      {!isConnected && (
        <button
          onClick={checkConnection}
          className="mt-2 text-xs text-primary-600 hover:text-primary-800 font-medium"
        >
          Retry Connection
        </button>
      )}
    </div>
  );
};

export default ConnectionStatus;