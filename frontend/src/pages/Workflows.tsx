import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  PlayIcon,
  PauseIcon,
  PencilIcon,
  TrashIcon,
  PlusIcon,
  MagnifyingGlassIcon,
  EyeIcon,
} from '@heroicons/react/24/outline';
import { useApi } from '../contexts/ApiContext';
import toast from 'react-hot-toast';

interface Workflow {
  id: string;
  name: string;
  active: boolean;
  createdAt: string;
  updatedAt: string;
  tags?: Array<{ id: string; name: string }>;
  nodes?: any[];
}

const Workflows: React.FC = () => {
  const { n8nApi, isConnected } = useApi();
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterActive, setFilterActive] = useState<'all' | 'active' | 'inactive'>('all');

  useEffect(() => {
    if (isConnected) {
      fetchWorkflows();
    }
  }, [isConnected]);

  const fetchWorkflows = async () => {
    try {
      setLoading(true);
      const response = await n8nApi.get('/workflows');
      setWorkflows(response.data.data || []);
    } catch (error) {
      console.error('Failed to fetch workflows:', error);
      toast.error('Failed to load workflows');
    } finally {
      setLoading(false);
    }
  };

  const toggleWorkflow = async (id: string, currentActive: boolean) => {
    try {
      await n8nApi.patch(`/workflows/${id}`, {
        active: !currentActive,
      });
      
      setWorkflows(workflows.map(w => 
        w.id === id ? { ...w, active: !currentActive } : w
      ));
      
      toast.success(`Workflow ${!currentActive ? 'activated' : 'deactivated'}`);
    } catch (error) {
      console.error('Failed to toggle workflow:', error);
      toast.error('Failed to update workflow');
    }
  };

  const executeWorkflow = async (id: string) => {
    try {
      await n8nApi.post(`/workflows/${id}/execute`);
      toast.success('Workflow execution started');
    } catch (error) {
      console.error('Failed to execute workflow:', error);
      toast.error('Failed to execute workflow');
    }
  };

  const deleteWorkflow = async (id: string, name: string) => {
    if (!window.confirm(`Are you sure you want to delete "${name}"?`)) {
      return;
    }

    try {
      await n8nApi.delete(`/workflows/${id}`);
      setWorkflows(workflows.filter(w => w.id !== id));
      toast.success('Workflow deleted successfully');
    } catch (error) {
      console.error('Failed to delete workflow:', error);
      toast.error('Failed to delete workflow');
    }
  };

  const filteredWorkflows = workflows.filter(workflow => {
    const matchesSearch = workflow.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterActive === 'all' || 
                         (filterActive === 'active' && workflow.active) ||
                         (filterActive === 'inactive' && !workflow.active);
    return matchesSearch && matchesFilter;
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
            Workflows
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Manage and execute your n8n workflows
          </p>
        </div>
        <div className="mt-4 flex md:mt-0 md:ml-4 space-x-3">
          <button
            onClick={fetchWorkflows}
            disabled={loading}
            className="btn-outline"
          >
            Refresh
          </button>
          <a
            href="https://n8n.unit-y-ai.io"
            target="_blank"
            rel="noopener noreferrer"
            className="btn-primary"
          >
            <PlusIcon className="h-4 w-4 mr-2" />
            Create Workflow
          </a>
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
                placeholder="Search workflows..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>
          <div className="flex space-x-2">
            <select
              className="input"
              value={filterActive}
              onChange={(e) => setFilterActive(e.target.value as any)}
            >
              <option value="all">All Workflows</option>
              <option value="active">Active Only</option>
              <option value="inactive">Inactive Only</option>
            </select>
          </div>
        </div>
      </div>

      {/* Workflows List */}
      <div className="bg-white shadow-sm rounded-lg border border-gray-200">
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-2 text-sm text-gray-500">Loading workflows...</p>
          </div>
        ) : filteredWorkflows.length === 0 ? (
          <div className="text-center py-12">
            <PlayIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No workflows found</h3>
            <p className="mt-1 text-sm text-gray-500">
              {searchTerm || filterActive !== 'all' 
                ? 'Try adjusting your search or filters.'
                : 'Get started by creating your first workflow.'}
            </p>
          </div>
        ) : (
          <div className="overflow-hidden">
            <ul className="divide-y divide-gray-200">
              {filteredWorkflows.map((workflow) => (
                <li key={workflow.id} className="px-6 py-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="flex-shrink-0">
                        <div className={`w-3 h-3 rounded-full ${
                          workflow.active ? 'bg-success-400' : 'bg-gray-300'
                        }`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-3">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {workflow.name}
                          </p>
                          <span className={`badge ${
                            workflow.active ? 'badge-success' : 'badge-secondary'
                          }`}>
                            {workflow.active ? 'Active' : 'Inactive'}
                          </span>
                        </div>
                        <div className="flex items-center space-x-4 mt-1">
                          <p className="text-sm text-gray-500">
                            Updated: {new Date(workflow.updatedAt).toLocaleDateString()}
                          </p>
                          {workflow.nodes && (
                            <p className="text-sm text-gray-500">
                              {workflow.nodes.length} nodes
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Link
                        to={`/workflows/${workflow.id}`}
                        className="p-2 text-gray-400 hover:text-gray-600"
                        title="View Details"
                      >
                        <EyeIcon className="h-5 w-5" />
                      </Link>
                      <button
                        onClick={() => executeWorkflow(workflow.id)}
                        className="p-2 text-primary-600 hover:text-primary-800"
                        title="Execute Workflow"
                      >
                        <PlayIcon className="h-5 w-5" />
                      </button>
                      <button
                        onClick={() => toggleWorkflow(workflow.id, workflow.active)}
                        className={`p-2 ${
                          workflow.active 
                            ? 'text-warning-600 hover:text-warning-800'
                            : 'text-success-600 hover:text-success-800'
                        }`}
                        title={workflow.active ? 'Deactivate' : 'Activate'}
                      >
                        {workflow.active ? (
                          <PauseIcon className="h-5 w-5" />
                        ) : (
                          <PlayIcon className="h-5 w-5" />
                        )}
                      </button>
                      <a
                        href={`https://n8n.unit-y-ai.io/workflow/${workflow.id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-2 text-gray-400 hover:text-gray-600"
                        title="Edit in n8n"
                      >
                        <PencilIcon className="h-5 w-5" />
                      </a>
                      <button
                        onClick={() => deleteWorkflow(workflow.id, workflow.name)}
                        className="p-2 text-error-600 hover:text-error-800"
                        title="Delete Workflow"
                      >
                        <TrashIcon className="h-5 w-5" />
                      </button>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

export default Workflows;