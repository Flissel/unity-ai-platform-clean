import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  PlayIcon,
  MagnifyingGlassIcon,
  EyeIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import { useApi } from '../contexts/ApiContext';
import toast from 'react-hot-toast';

interface Execution {
  id: string;
  workflowId: string;
  workflowName?: string;
  mode: string;
  status: 'success' | 'error' | 'running' | 'waiting' | 'canceled';
  startedAt: string;
  stoppedAt?: string;
  executionTime?: number;
  data?: any;
}

const Executions: React.FC = () => {
  const { n8nApi, isConnected } = useApi();
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const itemsPerPage = 20;

  useEffect(() => {
    if (isConnected) {
      fetchExecutions();
    }
  }, [isConnected, currentPage, statusFilter]);

  const fetchExecutions = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        limit: itemsPerPage.toString(),
        offset: ((currentPage - 1) * itemsPerPage).toString(),
      });
      
      if (statusFilter !== 'all') {
        params.append('status', statusFilter);
      }

      const response = await n8nApi.get(`/executions?${params}`);
      const data = response.data;
      
      setExecutions(data.data || []);
      setTotalPages(Math.ceil((data.count || 0) / itemsPerPage));
    } catch (error) {
      console.error('Failed to fetch executions:', error);
      toast.error('Failed to load executions');
    } finally {
      setLoading(false);
    }
  };

  const retryExecution = async (executionId: string) => {
    try {
      await n8nApi.post(`/executions/${executionId}/retry`);
      toast.success('Execution retry started');
      fetchExecutions();
    } catch (error) {
      console.error('Failed to retry execution:', error);
      toast.error('Failed to retry execution');
    }
  };

  const deleteExecution = async (executionId: string) => {
    if (!window.confirm('Are you sure you want to delete this execution?')) {
      return;
    }

    try {
      await n8nApi.delete(`/executions/${executionId}`);
      toast.success('Execution deleted successfully');
      fetchExecutions();
    } catch (error) {
      console.error('Failed to delete execution:', error);
      toast.error('Failed to delete execution');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircleIcon className="h-5 w-5 text-success-500" />;
      case 'error':
        return <XCircleIcon className="h-5 w-5 text-error-500" />;
      case 'running':
        return <ArrowPathIcon className="h-5 w-5 text-primary-500 animate-spin" />;
      case 'waiting':
        return <ClockIcon className="h-5 w-5 text-warning-500" />;
      default:
        return <XCircleIcon className="h-5 w-5 text-gray-400" />;
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

  const filteredExecutions = executions.filter(execution => {
    const matchesSearch = execution.workflowName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         execution.id.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesSearch;
  });

  if (!isConnected) {
    return (
      <div className="text-center py-12">
        <PlayIcon className="mx-auto h-12 w-12 text-gray-400" />
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
            Executions
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            View and manage workflow execution history
          </p>
        </div>
        <div className="mt-4 flex md:mt-0 md:ml-4">
          <button
            onClick={fetchExecutions}
            disabled={loading}
            className="btn-outline"
          >
            <ArrowPathIcon className="h-4 w-4 mr-2" />
            Refresh
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-3 sm:space-y-0 sm:space-x-4">
          <div className="flex-1">
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                className="input pl-10"
                placeholder="Search executions..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>
          <div className="flex space-x-2">
            <select
              className="input"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="all">All Status</option>
              <option value="success">Success</option>
              <option value="error">Error</option>
              <option value="running">Running</option>
              <option value="waiting">Waiting</option>
            </select>
          </div>
        </div>
      </div>

      {/* Executions List */}
      <div className="bg-white shadow-sm rounded-lg border border-gray-200">
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-2 text-sm text-gray-500">Loading executions...</p>
          </div>
        ) : filteredExecutions.length === 0 ? (
          <div className="text-center py-12">
            <ClockIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No executions found</h3>
            <p className="mt-1 text-sm text-gray-500">
              {searchTerm || statusFilter !== 'all' 
                ? 'Try adjusting your search or filters.'
                : 'No workflow executions yet.'}
            </p>
          </div>
        ) : (
          <div className="overflow-hidden">
            <ul className="divide-y divide-gray-200">
              {filteredExecutions.map((execution) => (
                <li key={execution.id} className="px-6 py-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="flex-shrink-0">
                        {getStatusIcon(execution.status)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-3">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {execution.workflowName || `Workflow ${execution.workflowId}`}
                          </p>
                          <span className={getStatusBadge(execution.status)}>
                            {execution.status}
                          </span>
                        </div>
                        <div className="flex items-center space-x-4 mt-1">
                          <p className="text-sm text-gray-500">
                            Started: {new Date(execution.startedAt).toLocaleString()}
                          </p>
                          {execution.executionTime && (
                            <p className="text-sm text-gray-500">
                              Duration: {formatDuration(execution.executionTime)}
                            </p>
                          )}
                          <p className="text-sm text-gray-500">
                            Mode: {execution.mode}
                          </p>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Link
                        to={`/executions/${execution.id}`}
                        className="p-2 text-gray-400 hover:text-gray-600"
                        title="View Details"
                      >
                        <EyeIcon className="h-5 w-5" />
                      </Link>
                      {execution.status === 'error' && (
                        <button
                          onClick={() => retryExecution(execution.id)}
                          className="p-2 text-primary-600 hover:text-primary-800"
                          title="Retry Execution"
                        >
                          <ArrowPathIcon className="h-5 w-5" />
                        </button>
                      )}
                      <button
                        onClick={() => deleteExecution(execution.id)}
                        className="p-2 text-error-600 hover:text-error-800"
                        title="Delete Execution"
                      >
                        <XCircleIcon className="h-5 w-5" />
                      </button>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex-1 flex justify-between sm:hidden">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className="btn-outline"
            >
              Previous
            </button>
            <button
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              className="btn-outline"
            >
              Next
            </button>
          </div>
          <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
            <div>
              <p className="text-sm text-gray-700">
                Showing page <span className="font-medium">{currentPage}</span> of{' '}
                <span className="font-medium">{totalPages}</span>
              </p>
            </div>
            <div>
              <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                <button
                  onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                  disabled={currentPage === 1}
                  className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                >
                  Previous
                </button>
                <button
                  onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                  disabled={currentPage === totalPages}
                  className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                >
                  Next
                </button>
              </nav>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Executions;