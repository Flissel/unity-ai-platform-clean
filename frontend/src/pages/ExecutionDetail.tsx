import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeftIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  PlayIcon,
  ArrowPathIcon,
  DocumentTextIcon,
  ExclamationTriangleIcon,
  ChevronDownIcon,
  ChevronRightIcon,
} from '@heroicons/react/24/outline';
import { useApi } from '../contexts/ApiContext';
import toast from 'react-hot-toast';

interface ExecutionDetail {
  id: string;
  workflowId: string;
  workflowName?: string;
  mode: string;
  status: 'success' | 'error' | 'running' | 'waiting' | 'canceled';
  startedAt: string;
  stoppedAt?: string;
  executionTime?: number;
  data: {
    resultData: {
      runData: Record<string, Array<{
        data: {
          main: Array<Array<any>>;
        };
        executionTime: number;
        source: Array<{
          previousNode: string;
        }>;
      }>>;
    };
    executionData?: {
      contextData: any;
      nodeExecutionStack: any[];
      metadata: any;
      waitingExecution: any;
      waitingExecutionSource: any;
    };
  };
}

interface NodeExecution {
  nodeName: string;
  status: 'success' | 'error' | 'running';
  executionTime: number;
  data: any[];
  error?: string;
}

const ExecutionDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { n8nApi, isConnected } = useApi();
  const [execution, setExecution] = useState<ExecutionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'nodes' | 'data'>('overview');
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (isConnected && id) {
      fetchExecution();
    }
  }, [isConnected, id]);

  const fetchExecution = async () => {
    try {
      setLoading(true);
      const response = await n8nApi.get(`/executions/${id}`);
      setExecution(response.data);
    } catch (error) {
      console.error('Failed to fetch execution:', error);
      toast.error('Failed to load execution details');
    } finally {
      setLoading(false);
    }
  };

  const retryExecution = async () => {
    try {
      await n8nApi.post(`/executions/${id}/retry`);
      toast.success('Execution retry started');
      // Refresh execution details after a short delay
      setTimeout(fetchExecution, 2000);
    } catch (error) {
      console.error('Failed to retry execution:', error);
      toast.error('Failed to retry execution');
    }
  };

  const getStatusIcon = (status: string, size: string = 'h-5 w-5') => {
    switch (status) {
      case 'success':
        return <CheckCircleIcon className={`${size} text-success-500`} />;
      case 'error':
        return <XCircleIcon className={`${size} text-error-500`} />;
      case 'running':
        return <div className={`${size} border-2 border-primary-500 border-t-transparent rounded-full animate-spin`} />;
      case 'waiting':
        return <ClockIcon className={`${size} text-warning-500`} />;
      default:
        return <ExclamationTriangleIcon className={`${size} text-gray-400`} />;
    }
  };

  const getStatusBadge = (status: string) => {
    const baseClasses = 'badge';
    switch (status) {
      case 'success':
        return `${baseClasses} badge-success`;
      case 'error':
        return `${baseClasses} badge-error`;
      case 'running':
        return `${baseClasses} badge-primary`;
      case 'waiting':
        return `${baseClasses} badge-warning`;
      default:
        return `${baseClasses} badge-secondary`;
    }
  };

  const formatDuration = (ms?: number) => {
    if (!ms) return 'N/A';
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
  };

  const getNodeExecutions = (): NodeExecution[] => {
    if (!execution?.data?.resultData?.runData) return [];
    
    return Object.entries(execution.data.resultData.runData).map(([nodeName, nodeData]) => {
      const latestRun = nodeData[nodeData.length - 1];
      return {
        nodeName,
        status: 'success', // Simplified - in real implementation, check for errors
        executionTime: latestRun?.executionTime || 0,
        data: latestRun?.data?.main?.[0] || [],
      };
    });
  };

  const toggleNodeExpansion = (nodeName: string) => {
    const newExpanded = new Set(expandedNodes);
    if (newExpanded.has(nodeName)) {
      newExpanded.delete(nodeName);
    } else {
      newExpanded.add(nodeName);
    }
    setExpandedNodes(newExpanded);
  };

  if (!isConnected) {
    return (
      <div className="text-center py-12">
        <XCircleIcon className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">Not Connected</h3>
        <p className="mt-1 text-sm text-gray-500">
          Please check your connection to the n8n API.
        </p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
        <p className="mt-2 text-sm text-gray-500">Loading execution details...</p>
      </div>
    );
  }

  if (!execution) {
    return (
      <div className="text-center py-12">
        <XCircleIcon className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">Execution Not Found</h3>
        <p className="mt-1 text-sm text-gray-500">
          The requested execution could not be found.
        </p>
        <Link to="/executions" className="mt-4 btn-primary inline-flex items-center">
          <ArrowLeftIcon className="h-4 w-4 mr-2" />
          Back to Executions
        </Link>
      </div>
    );
  }

  const nodeExecutions = getNodeExecutions();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link
            to="/executions"
            className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
          >
            <ArrowLeftIcon className="h-5 w-5" />
          </Link>
          <div>
            <div className="flex items-center space-x-3">
              <h1 className="text-2xl font-bold text-gray-900">
                {execution.workflowName || `Workflow ${execution.workflowId}`}
              </h1>
              <span className={getStatusBadge(execution.status)}>
                {execution.status}
              </span>
            </div>
            <p className="text-sm text-gray-500 mt-1">
              Execution ID: {execution.id}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          {execution.status === 'error' && (
            <button
              onClick={retryExecution}
              className="btn-primary"
            >
              <ArrowPathIcon className="h-4 w-4 mr-2" />
              Retry
            </button>
          )}
          <Link
            to={`/workflows/${execution.workflowId}`}
            className="btn-outline"
          >
            View Workflow
          </Link>
        </div>
      </div>

      {/* Status Overview */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="flex items-center space-x-3">
            {getStatusIcon(execution.status)}
            <div>
              <p className="text-sm font-medium text-gray-900">Status</p>
              <p className="text-sm text-gray-500 capitalize">{execution.status}</p>
            </div>
          </div>
          
          <div>
            <p className="text-sm font-medium text-gray-900">Started</p>
            <p className="text-sm text-gray-500">
              {new Date(execution.startedAt).toLocaleString()}
            </p>
          </div>
          
          <div>
            <p className="text-sm font-medium text-gray-900">Duration</p>
            <p className="text-sm text-gray-500">
              {formatDuration(execution.executionTime)}
            </p>
          </div>
          
          <div>
            <p className="text-sm font-medium text-gray-900">Mode</p>
            <p className="text-sm text-gray-500 capitalize">{execution.mode}</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', name: 'Overview', icon: DocumentTextIcon },
            { id: 'nodes', name: 'Node Executions', icon: PlayIcon },
            { id: 'data', name: 'Raw Data', icon: DocumentTextIcon },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <tab.icon className="h-4 w-4 mr-2" />
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        {activeTab === 'overview' && (
          <div className="p-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Execution Summary</h3>
                <dl className="space-y-3">
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Workflow ID</dt>
                    <dd className="text-sm text-gray-900 font-mono">{execution.workflowId}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Execution ID</dt>
                    <dd className="text-sm text-gray-900 font-mono">{execution.id}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Started At</dt>
                    <dd className="text-sm text-gray-900">
                      {new Date(execution.startedAt).toLocaleString()}
                    </dd>
                  </div>
                  {execution.stoppedAt && (
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Stopped At</dt>
                      <dd className="text-sm text-gray-900">
                        {new Date(execution.stoppedAt).toLocaleString()}
                      </dd>
                    </div>
                  )}
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Execution Time</dt>
                    <dd className="text-sm text-gray-900">
                      {formatDuration(execution.executionTime)}
                    </dd>
                  </div>
                </dl>
              </div>
              
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Node Statistics</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-500">Total Nodes</span>
                    <span className="text-sm font-medium text-gray-900">{nodeExecutions.length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-500">Successful</span>
                    <span className="text-sm font-medium text-success-600">
                      {nodeExecutions.filter(n => n.status === 'success').length}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-500">Failed</span>
                    <span className="text-sm font-medium text-error-600">
                      {nodeExecutions.filter(n => n.status === 'error').length}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-500">Total Execution Time</span>
                    <span className="text-sm font-medium text-gray-900">
                      {formatDuration(nodeExecutions.reduce((sum, n) => sum + n.executionTime, 0))}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'nodes' && (
          <div className="p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Node Executions</h3>
            {nodeExecutions.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-8">No node execution data available</p>
            ) : (
              <div className="space-y-3">
                {nodeExecutions.map((node) => (
                  <div key={node.nodeName} className="border border-gray-200 rounded-lg">
                    <button
                      onClick={() => toggleNodeExpansion(node.nodeName)}
                      className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50"
                    >
                      <div className="flex items-center space-x-3">
                        {getStatusIcon(node.status, 'h-4 w-4')}
                        <div>
                          <p className="text-sm font-medium text-gray-900">{node.nodeName}</p>
                          <p className="text-xs text-gray-500">
                            {formatDuration(node.executionTime)} • {node.data.length} items
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className={getStatusBadge(node.status)}>
                          {node.status}
                        </span>
                        {expandedNodes.has(node.nodeName) ? (
                          <ChevronDownIcon className="h-4 w-4 text-gray-400" />
                        ) : (
                          <ChevronRightIcon className="h-4 w-4 text-gray-400" />
                        )}
                      </div>
                    </button>
                    
                    {expandedNodes.has(node.nodeName) && (
                      <div className="border-t border-gray-200 p-4 bg-gray-50">
                        <h4 className="text-sm font-medium text-gray-900 mb-2">Output Data</h4>
                        {node.data.length === 0 ? (
                          <p className="text-sm text-gray-500">No output data</p>
                        ) : (
                          <div className="bg-white rounded border p-3 max-h-64 overflow-auto">
                            <pre className="text-xs text-gray-700 whitespace-pre-wrap">
                              {JSON.stringify(node.data, null, 2)}
                            </pre>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'data' && (
          <div className="p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Raw Execution Data</h3>
            <div className="bg-gray-50 rounded-lg p-4 max-h-96 overflow-auto">
              <pre className="text-xs text-gray-700 whitespace-pre-wrap">
                {JSON.stringify(execution.data, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ExecutionDetail;