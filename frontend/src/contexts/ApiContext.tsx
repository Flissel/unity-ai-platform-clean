import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import axios, { AxiosInstance } from 'axios';
import toast from 'react-hot-toast';

interface ApiContextType {
  n8nApi: AxiosInstance;
  playgroundApi: AxiosInstance;
  isConnected: boolean;
  isLoading: boolean;
  checkConnection: () => Promise<void>;
}

const ApiContext = createContext<ApiContextType | undefined>(undefined);

interface ApiProviderProps {
  children: ReactNode;
}

// API Configuration from environment variables

export const ApiProvider: React.FC<ApiProviderProps> = ({ children }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Create axios instances for both APIs
  const n8nApi = axios.create({
    baseURL: process.env.REACT_APP_N8N_API_URL || 'https://n8n.unit-y-ai.io/api/v1',
    headers: {
      'Content-Type': 'application/json',
      'X-N8N-API-KEY': process.env.REACT_APP_N8N_API_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4OTI3MDE4NC1jYjIyLTQwZGQtYTljMS1hNjVlMzgxMjFjY2EiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzQ5MTk0MDE2fQ.VgtrtX9jNjYj5z_WfHo2Lv9Flm9bQuB1hSY_JfITlKI',
    },
    timeout: 10000,
  });

  const playgroundApi = axios.create({
    baseURL: process.env.REACT_APP_PLAYGROUND_API_URL || 'http://localhost:8000',
    headers: {
      'Content-Type': 'application/json',
    },
    timeout: 10000,
  });

  // Add response interceptors for error handling
  n8nApi.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK') {
        setIsConnected(false);
        toast.error('Cannot connect to n8n API');
      } else if (error.response?.status === 401) {
        toast.error('Invalid API key');
      } else if (error.response?.status >= 500) {
        toast.error('n8n server error');
      }
      return Promise.reject(error);
    }
  );

  playgroundApi.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK') {
        toast.error('Cannot connect to playground API');
      }
      return Promise.reject(error);
    }
  );

  const checkConnection = async () => {
    setIsLoading(true);
    try {
      // Test n8n API connection
      await n8nApi.get('/workflows');
      setIsConnected(true);
      toast.success('Connected to n8n API successfully!');
    } catch (error) {
      setIsConnected(false);
      console.error('Connection test failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    checkConnection();
  }, []);

  const value: ApiContextType = {
    playgroundApi,
    n8nApi,
    isConnected,
    isLoading,
    checkConnection,
  };

  return (
    <ApiContext.Provider value={value}>
      {children}
    </ApiContext.Provider>
  );
};

export const useApi = (): ApiContextType => {
  const context = useContext(ApiContext);
  if (context === undefined) {
    throw new Error('useApi must be used within an ApiProvider');
  }
  return context;
};