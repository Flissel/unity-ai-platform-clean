import React, { useState, useEffect } from 'react';
import {
  KeyIcon,
  PlusIcon,
  PencilIcon,
  TrashIcon,
  MagnifyingGlassIcon,
  EyeIcon,
  EyeSlashIcon,
  ShieldCheckIcon,
} from '@heroicons/react/24/outline';
import { useApi } from '../contexts/ApiContext';
import toast from 'react-hot-toast';

interface Credential {
  id: string;
  name: string;
  type: string;
  nodesAccess: Array<{
    nodeType: string;
  }>;
  sharedWith: Array<{
    id: string;
    firstName: string;
    lastName: string;
  }>;
  createdAt: string;
  updatedAt: string;
}

const Credentials: React.FC = () => {
  const { n8nApi, isConnected } = useApi();
  const [credentials, setCredentials] = useState<Credential[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [showDetails, setShowDetails] = useState<string | null>(null);

  useEffect(() => {
    if (isConnected) {
      fetchCredentials();
    }
  }, [isConnected]);

  const fetchCredentials = async () => {
    try {
      setLoading(true);
      const response = await n8nApi.get('/credentials');
      setCredentials(response.data.data || []);
    } catch (error) {
      console.error('Failed to fetch credentials:', error);
      toast.error('Failed to load credentials');
    } finally {
      setLoading(false);
    }
  };

  const deleteCredential = async (id: string, name: string) => {
    if (!window.confirm(`Are you sure you want to delete "${name}"?`)) {
      return;
    }

    try {
      await n8nApi.delete(`/credentials/${id}`);
      setCredentials(credentials.filter(c => c.id !== id));
      toast.success('Credential deleted successfully');
    } catch (error) {
      console.error('Failed to delete credential:', error);
      toast.error('Failed to delete credential');
    }
  };

  const getCredentialTypes = () => {
    const types = Array.from(new Set(credentials.map(c => c.type)));
    return types.sort();
  };

  const filteredCredentials = credentials.filter(credential => {
    const matchesSearch = credential.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         credential.type.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = typeFilter === 'all' || credential.type === typeFilter;
    return matchesSearch && matchesType;
  });

  const formatCredentialType = (type: string) => {
    return type.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase());
  };

  if (!isConnected) {
    return (
      <div className="text-center py-12">
        <KeyIcon className="mx-auto h-12 w-12 text-gray-400" />
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
            Credentials
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Manage your n8n credentials and API keys
          </p>
        </div>
        <div className="mt-4 flex md:mt-0 md:ml-4 space-x-3">
          <button
            onClick={fetchCredentials}
            disabled={loading}
            className="btn-outline"
          >
            Refresh
          </button>
          <a
            href="https://n8n.unit-y-ai.io/credentials"
            target="_blank"
            rel="noopener noreferrer"
            className="btn-primary"
          >
            <PlusIcon className="h-4 w-4 mr-2" />
            Create Credential
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
                placeholder="Search credentials..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>
          <div className="flex space-x-2">
            <select
              className="input"
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
            >
              <option value="all">All Types</option>
              {getCredentialTypes().map(type => (
                <option key={type} value={type}>
                  {formatCredentialType(type)}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Credentials List */}
      <div className="bg-white shadow-sm rounded-lg border border-gray-200">
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-2 text-sm text-gray-500">Loading credentials...</p>
          </div>
        ) : filteredCredentials.length === 0 ? (
          <div className="text-center py-12">
            <KeyIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No credentials found</h3>
            <p className="mt-1 text-sm text-gray-500">
              {searchTerm || typeFilter !== 'all' 
                ? 'Try adjusting your search or filters.'
                : 'Get started by creating your first credential.'}
            </p>
          </div>
        ) : (
          <div className="overflow-hidden">
            <ul className="divide-y divide-gray-200">
              {filteredCredentials.map((credential) => (
                <li key={credential.id} className="px-6 py-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="flex-shrink-0">
                        <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
                          <KeyIcon className="h-5 w-5 text-primary-600" />
                        </div>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-3">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {credential.name}
                          </p>
                          <span className="badge badge-secondary">
                            {formatCredentialType(credential.type)}
                          </span>
                          {credential.sharedWith.length > 0 && (
                            <span className="badge badge-primary">
                              Shared
                            </span>
                          )}
                        </div>
                        <div className="flex items-center space-x-4 mt-1">
                          <p className="text-sm text-gray-500">
                            Updated: {new Date(credential.updatedAt).toLocaleDateString()}
                          </p>
                          {credential.nodesAccess.length > 0 && (
                            <p className="text-sm text-gray-500">
                              {credential.nodesAccess.length} node type(s)
                            </p>
                          )}
                        </div>
                        
                        {/* Expandable Details */}
                        {showDetails === credential.id && (
                          <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              <div>
                                <h4 className="text-sm font-medium text-gray-900 mb-2">
                                  Node Access
                                </h4>
                                {credential.nodesAccess.length > 0 ? (
                                  <ul className="text-sm text-gray-600 space-y-1">
                                    {credential.nodesAccess.map((node, index) => (
                                      <li key={index} className="flex items-center">
                                        <ShieldCheckIcon className="h-4 w-4 text-success-500 mr-2" />
                                        {node.nodeType}
                                      </li>
                                    ))}
                                  </ul>
                                ) : (
                                  <p className="text-sm text-gray-500">No specific node access</p>
                                )}
                              </div>
                              
                              <div>
                                <h4 className="text-sm font-medium text-gray-900 mb-2">
                                  Shared With
                                </h4>
                                {credential.sharedWith.length > 0 ? (
                                  <ul className="text-sm text-gray-600 space-y-1">
                                    {credential.sharedWith.map((user) => (
                                      <li key={user.id} className="flex items-center">
                                        <div className="w-6 h-6 bg-primary-100 rounded-full flex items-center justify-center mr-2">
                                          <span className="text-xs font-medium text-primary-600">
                                            {user.firstName.charAt(0)}
                                          </span>
                                        </div>
                                        {user.firstName} {user.lastName}
                                      </li>
                                    ))}
                                  </ul>
                                ) : (
                                  <p className="text-sm text-gray-500">Not shared</p>
                                )}
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => setShowDetails(
                          showDetails === credential.id ? null : credential.id
                        )}
                        className="p-2 text-gray-400 hover:text-gray-600"
                        title={showDetails === credential.id ? 'Hide Details' : 'Show Details'}
                      >
                        {showDetails === credential.id ? (
                          <EyeSlashIcon className="h-5 w-5" />
                        ) : (
                          <EyeIcon className="h-5 w-5" />
                        )}
                      </button>
                      <a
                        href={`https://n8n.unit-y-ai.io/credentials/${credential.id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-2 text-gray-400 hover:text-gray-600"
                        title="Edit in n8n"
                      >
                        <PencilIcon className="h-5 w-5" />
                      </a>
                      <button
                        onClick={() => deleteCredential(credential.id, credential.name)}
                        className="p-2 text-error-600 hover:text-error-800"
                        title="Delete Credential"
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

      {/* Security Notice */}
      <div className="bg-warning-50 border border-warning-200 rounded-lg p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <ShieldCheckIcon className="h-5 w-5 text-warning-400" />
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-warning-800">
              Security Notice
            </h3>
            <div className="mt-2 text-sm text-warning-700">
              <p>
                Credentials are securely stored and encrypted. Only authorized users can access and modify them.
                Always use the principle of least privilege when sharing credentials.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Credentials;