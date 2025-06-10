import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeftIcon,
  PlayIcon,
  PauseIcon,
  PencilIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  CogIcon,
  EyeIcon,
} from '@heroicons/react/24/outline';
import { useApi } from '../contexts/ApiContext';
import toast from 'react-hot-toast';

interface WorkflowDetail {
  id: string;
  name: string;
  active: boolean;
  createdAt: string;
  updatedAt: string;
  tags?: Array<{ id: string; name: string }>;
  nodes: Array<{
    id: string;
    name: string;
    type: string;
    position: [number, number];
    parameters: any;
  }>;
  connections: any;
  settings: {
    executionOrder: string;
    saveManualExecutions: boolean;
    saveExecutionProgress: boolean;
    saveDataErrorExecution: string;
    saveDataSuccessExecution: string;
    executionTimeout: number;
    timezone: string;
  };
}

interface RecentExecution {
  id: string;
  status: string;
  startedAt: string;
  stoppedAt?: string;
  executionTime?: number;
  mode: string;
}

const WorkflowDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { n8nApi, isConnected } = useApi();
  const [workflow, setWorkflow] = useState<WorkflowDetail | null>(null);
  const [recentExecutions, setRecentExecutions] = useState<RecentExecution[]>([]);
  const [loading, setLoading] = useState(true);
  const [executionsLoading, setExecutionsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'nodes' | 'executions' | 'settings'>('overview');

  useEffect(() => {
    if (isConnected && id) {
      fetchWorkflow();
      fetchRecentExecutions();
    }
  }, [isConnected, id]);

  const fetchWorkflow = async () => {
    try {
      setLoading(true);
      const response = await n8nApi.get(`/workflows/${id}`);
      setWorkflow(response.data);
    } catch (error) {
      console.error('Failed to fetch workflow:', error);
      toast.error('Failed to load workflow details');
    } finally {
      setLoading(false);
    }
  };

  const fetchRecentExecutions = async () => {
    try {
      setExecutionsLoading(true);
      const response = await n8nApi.get(`/executions?workflowId=${id}&limit=10`);
      setRecentExecutions(response.data.data || []);
    } catch (error) {
      console.error('Failed to fetch executions:', error);
    } finally {
      setExecutionsLoading(false);
    }
  };

  const toggleWorkflow = async () => {
    if (!workflow) return;
    
    try {
      await n8nApi.patch(`/workflows/${id}`, {
        active: !workflow.active,
      });
      
      setWorkflow({ ...workflow, active: !workflow.active });
      toast.success(`Workflow ${!workflow.active ? 'activated' : 'deactivated'}`);
    } catch (error) {
      console.error('Failed to toggle workflow:', error);
      toast.error('Failed to update workflow');
    }
  };

  const executeWorkflow = async () => {
    try {
      await n8nApi.post(`/workflows/${id}/execute`);
      toast.success('Workflow execution started');
      // Refresh executions after a short delay
      setTimeout(fetchRecentExecutions, 2000);
    } catch (error) {
      console.error('Failed to execute workflow:', error);
      toast.error('Failed to execute workflow');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircleIcon className="h-4 w-4 text-success-500" />;
      case 'error':
        return <XCircleIcon className="h-4 w-4 text-error-500" />;
      case 'running':
        return <div className="h-4 w-4 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />;
      default:
        return <ClockIcon className="h-4 w-4 text-gray-400" />;
    }
  };

  const formatDuration = (ms?: number) => {
    if (!ms) return 'N/A';
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
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
        <p className="mt-2 text-sm text-gray-500">Loading workflow details...</p>
      </div>
    );
  }

  if (!workflow) {
    return (
      <div className="text-center py-12">
        <XCircleIcon className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">Workflow Not Found</h3>
        <p className="mt-1 text-sm text-gray-500">
          The requested workflow could not be found.
        </p>
        <Link to="/workflows" className="mt-4 btn-primary inline-flex items-center">
          <ArrowLeftIcon className="h-4 w-4 mr-2" />
          Back to Workflows
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link
            to="/workflows"
            className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
          >
            <ArrowLeftIcon className="h-5 w-5" />
          </Link>
          <div>
            <div className="flex items-center space-x-3">
              <h1 className="text-2xl font-bold text-gray-900">{workflow.name}</h1>
              <span className={`badge ${
                workflow.active ? 'badge-success' : 'badge-secondary'
              }`}>
                {workflow.active ? 'Active' : 'Inactive'}
              </span>
            </div>
            <p className="text-sm text-gray-500 mt-1">
              Last updated: {new Date(workflow.updatedAt).toLocaleString()}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={executeWorkflow}
            className="btn-primary"
          >
            <PlayIcon className="h-4 w-4 mr-2" />
            Execute
          </button>
          <button
            onClick={toggleWorkflow}
            className={workflow.active ? 'btn-warning' : 'btn-success'}
          >
            {workflow.active ? (
              <><PauseIcon className="h-4 w-4 mr-2" />Deactivate</>
            ) : (
              <><PlayIcon className="h-4 w-4 mr-2" />Activate</>
            )}
          </button>
          <a
            href={`https://n8n.unit-y-ai.io/workflow/${workflow.id}`}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-outline"
          >
            <PencilIcon className="h-4 w-4 mr-2" />
            Edit in n8n
          </a>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', name: 'Overview', icon: EyeIcon },
            { id: 'nodes', name: 'Nodes', icon: CogIcon },
            { id: 'executions', name: 'Recent Executions', icon: ClockIcon },
            { id: 'settings', name: 'Settings', icon: CogIcon },
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
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="text-sm font-medium text-gray-900 mb-2">Workflow Info</h3>
                <dl className="space-y-2">
                  <div>
                    <dt className="text-xs text-gray-500">ID</dt>
                    <dd className="text-sm text-gray-900 font-mono">{workflow.id}</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-gray-500">Created</dt>
                    <dd className="text-sm text-gray-900">
                      {new Date(workflow.createdAt).toLocaleDateString()}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs text-gray-500">Nodes</dt>
                    <dd className="text-sm text-gray-900">{workflow.nodes.length}</dd>
                  </div>
                </dl>
              </div>
              
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="text-sm font-medium text-gray-900 mb-2">Execution Settings</h3>
                <dl className="space-y-2">
                  <div>
                    <dt className="text-xs text-gray-500">Execution Order</dt>
                    <dd className="text-sm text-gray-900">{workflow.settings.executionOrder}</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-gray-500">Timeout</dt>
                    <dd className="text-sm text-gray-900">{workflow.settings.executionTimeout}s</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-gray-500">Timezone</dt>
                    <dd className="text-sm text-gray-900">{workflow.settings.timezone}</dd>
                  </div>
                </dl>
              </div>
              
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="text-sm font-medium text-gray-900 mb-2">Tags</h3>
                {workflow.tags && workflow.tags.length > 0 ? (
                  <div className="flex flex-wrap gap-1">
                    {workflow.tags.map((tag) => (
                      <span key={tag.id} className="badge badge-secondary text-xs">
                        {tag.name}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">No tags</p>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'nodes' && (
          <div className="p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Workflow Nodes</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {workflow.nodes.map((node) => (
                <div key={node.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-sm font-medium text-gray-900">{node.name}</h4>
                    <span className="badge badge-secondary text-xs">{node.type}</span>
                  </div>
                  <p className="text-xs text-gray-500 mb-2">ID: {node.id}</p>
                  <p className="text-xs text-gray-500">
                    Position: ({node.position[0]}, {node.position[1]})
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'executions' && (
          <div className="p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Executions</h3>
            {executionsLoading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600 mx-auto"></div>
                <p className="mt-2 text-sm text-gray-500">Loading executions...</p>
              </div>
            ) : recentExecutions.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-8">No executions found</p>
            ) : (
              <div className="space-y-3">
                {recentExecutions.map((execution) => (
                  <div key={execution.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      {getStatusIcon(execution.status)}
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {new Date(execution.startedAt).toLocaleString()}
                        </p>
                        <p className="text-xs text-gray-500">
                          {execution.mode} • {formatDuration(execution.executionTime)}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={`badge ${
                        execution.status === 'success' ? 'badge-success' :
                        execution.status === 'error' ? 'badge-error' :
                        execution.status === 'running' ? 'badge-primary' : 'badge-secondary'
                      }`}>
                        {execution.status}
                      </span>
                      <Link
                        to={`/executions/${execution.id}`}
                        className="p-1 text-gray-400 hover:text-gray-600"
                      >
                        <EyeIcon className="h-4 w-4" />
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Workflow Settings</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-3">Execution</h4>
                <dl className="space-y-3">
                  <div>
                    <dt className="text-sm text-gray-500">Execution Order</dt>
                    <dd className="text-sm text-gray-900">{workflow.settings.executionOrder}</dd>
                  </div>
                  <div>
                    <dt className="text-sm text-gray-500">Execution Timeout</dt>
                    <dd className="text-sm text-gray-900">{workflow.settings.executionTimeout} seconds</dd>
                  </div>
                  <div>
                    <dt className="text-sm text-gray-500">Timezone</dt>
                    <dd className="text-sm text-gray-900">{workflow.settings.timezone}</dd>
                  </div>
                </dl>
              </div>
              
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-3">Data Retention</h4>
                <dl className="space-y-3">
                  <div>
                    <dt className="text-sm text-gray-500">Save Manual Executions</dt>
                    <dd className="text-sm text-gray-900">
                      {workflow.settings.saveManualExecutions ? 'Yes' : 'No'}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm text-gray-500">Save Execution Progress</dt>
                    <dd className="text-sm text-gray-900">
                      {workflow.settings.saveExecutionProgress ? 'Yes' : 'No'}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm text-gray-500">Save Error Executions</dt>
                    <dd className="text-sm text-gray-900">{workflow.settings.saveDataErrorExecution}</dd>
                  </div>
                  <div>
                    <dt className="text-sm text-gray-500">Save Success Executions</dt>
                    <dd className="text-sm text-gray-900">{workflow.settings.saveDataSuccessExecution}</dd>
                  </div>
                </dl>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default WorkflowDetail;