import React, { useState, useEffect } from 'react';
import {
  PlayIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ChartBarIcon,
  BoltIcon,
} from '@heroicons/react/24/outline';
import { useApi } from '../contexts/ApiContext';
import toast from 'react-hot-toast';

interface DashboardStats {
  totalWorkflows: number;
  activeWorkflows: number;
  totalExecutions: number;
  successfulExecutions: number;
  failedExecutions: number;
  runningExecutions: number;
}

interface RecentExecution {
  id: string;
  workflowName: string;
  status: 'success' | 'error' | 'running' | 'waiting';
  startedAt: string;
  finishedAt?: string;
}

const Dashboard: React.FC = () => {
  const { n8nApi, isConnected } = useApi();
  const [stats, setStats] = useState<DashboardStats>({
    totalWorkflows: 0,
    activeWorkflows: 0,
    totalExecutions: 0,
    successfulExecutions: 0,
    failedExecutions: 0,
    runningExecutions: 0,
  });
  const [recentExecutions, setRecentExecutions] = useState<RecentExecution[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isConnected) {
      fetchDashboardData();
    }
  }, [isConnected]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch workflows
      const workflowsResponse = await n8nApi.get('/workflows');
      const workflows = workflowsResponse.data.data || [];
      
      // Fetch executions
      const executionsResponse = await n8nApi.get('/executions?limit=50');
      const executions = executionsResponse.data.data || [];
      
      // Calculate stats
      const activeWorkflows = workflows.filter((w: any) => w.active).length;
      const successfulExecutions = executions.filter((e: any) => e.finished && !e.stoppedAt).length;
      const failedExecutions = executions.filter((e: any) => e.stoppedAt).length;
      const runningExecutions = executions.filter((e: any) => !e.finished && !e.stoppedAt).length;
      
      setStats({
        totalWorkflows: workflows.length,
        activeWorkflows,
        totalExecutions: executions.length,
        successfulExecutions,
        failedExecutions,
        runningExecutions,
      });
      
      // Format recent executions
      const recent = executions.slice(0, 10).map((execution: any) => ({
        id: execution.id,
        workflowName: execution.workflowData?.name || 'Unknown Workflow',
        status: execution.finished && !execution.stoppedAt ? 'success' : 
                execution.stoppedAt ? 'error' : 'running',
        startedAt: execution.startedAt,
        finishedAt: execution.finishedAt,
      }));
      
      setRecentExecutions(recent);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircleIcon className="h-5 w-5 text-success-500" />;
      case 'error':
        return <ExclamationTriangleIcon className="h-5 w-5 text-error-500" />;
      case 'running':
        return <ClockIcon className="h-5 w-5 text-warning-500 animate-pulse" />;
      default:
        return <ClockIcon className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'success':
        return 'badge-success';
      case 'error':
        return 'badge-error';
      case 'running':
        return 'badge-warning';
      default:
        return 'badge-secondary';
    }
  };

  if (!isConnected) {
    return (
      <div className="text-center py-12">
        <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-error-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">Not Connected</h3>
        <p className="mt-1 text-sm text-gray-500">
          Please check your connection to the n8n API.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
            Dashboard
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Overview of your n8n workflows and executions
          </p>
        </div>
        <div className="mt-4 flex md:mt-0 md:ml-4">
          <button
            onClick={fetchDashboardData}
            disabled={loading}
            className="btn-primary"
          >
            {loading ? (
              <>
                <ClockIcon className="h-4 w-4 mr-2 animate-spin" />
                Refreshing...
              </>
            ) : (
              'Refresh'
            )}
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <PlayIcon className="h-8 w-8 text-primary-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Total Workflows
                </dt>
                <dd className="text-lg font-medium text-gray-900">
                  {stats.totalWorkflows}
                </dd>
              </dl>
            </div>
          </div>
          <div className="mt-3">
            <div className="text-sm text-gray-500">
              {stats.activeWorkflows} active
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ChartBarIcon className="h-8 w-8 text-success-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Total Executions
                </dt>
                <dd className="text-lg font-medium text-gray-900">
                  {stats.totalExecutions}
                </dd>
              </dl>
            </div>
          </div>
          <div className="mt-3">
            <div className="text-sm text-success-600">
              {stats.successfulExecutions} successful
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ExclamationTriangleIcon className="h-8 w-8 text-error-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Failed Executions
                </dt>
                <dd className="text-lg font-medium text-gray-900">
                  {stats.failedExecutions}
                </dd>
              </dl>
            </div>
          </div>
          <div className="mt-3">
            <div className="text-sm text-error-600">
              {((stats.failedExecutions / stats.totalExecutions) * 100 || 0).toFixed(1)}% failure rate
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <BoltIcon className="h-8 w-8 text-warning-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Running Now
                </dt>
                <dd className="text-lg font-medium text-gray-900">
                  {stats.runningExecutions}
                </dd>
              </dl>
            </div>
          </div>
          <div className="mt-3">
            <div className="text-sm text-warning-600">
              Active executions
            </div>
          </div>
        </div>
      </div>

      {/* Recent Executions */}
      <div className="card">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
            Recent Executions
          </h3>
          {loading ? (
            <div className="text-center py-4">
              <ClockIcon className="mx-auto h-8 w-8 text-gray-400 animate-spin" />
              <p className="mt-2 text-sm text-gray-500">Loading executions...</p>
            </div>
          ) : recentExecutions.length === 0 ? (
            <div className="text-center py-4">
              <ClockIcon className="mx-auto h-8 w-8 text-gray-400" />
              <p className="mt-2 text-sm text-gray-500">No executions found</p>
            </div>
          ) : (
            <div className="flow-root">
              <ul className="-my-5 divide-y divide-gray-200">
                {recentExecutions.map((execution) => (
                  <li key={execution.id} className="py-4">
                    <div className="flex items-center space-x-4">
                      <div className="flex-shrink-0">
                        {getStatusIcon(execution.status)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {execution.workflowName}
                        </p>
                        <p className="text-sm text-gray-500">
                          Started: {new Date(execution.startedAt).toLocaleString()}
                        </p>
                      </div>
                      <div className="flex-shrink-0">
                        <span className={`badge ${getStatusBadge(execution.status)}`}>
                          {execution.status}
                        </span>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;