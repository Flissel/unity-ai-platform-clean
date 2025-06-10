# UnityAI Frontend

A modern React-based frontend for controlling and monitoring the UnityAI n8n automation platform.

## Features

- 🎛️ **Full n8n Control**: Manage workflows, executions, and credentials
- 📊 **Real-time Dashboard**: Monitor system status and execution statistics
- 🎨 **Modern UI**: Beautiful, responsive design with Tailwind CSS
- 🔒 **Secure**: API key authentication and CORS protection
- 📱 **Mobile-friendly**: Responsive design for all devices
- ⚡ **Fast**: Optimized build with code splitting and caching

## Tech Stack

- **React 18** with TypeScript
- **Tailwind CSS** for styling
- **React Router** for navigation
- **Axios** for API communication
- **Heroicons** for icons
- **React Hot Toast** for notifications

## Quick Start

### Prerequisites

- Node.js 18+ and npm
- Access to n8n API at `https://n8n.unit-y-ai.io/api/v1`
- n8n API key (see setup instructions)

### Development Setup

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Set environment variables**:
   Create a `.env.local` file:
   ```env
   REACT_APP_N8N_API_URL=https://n8n.unit-y-ai.io/api/v1
   REACT_APP_PLAYGROUND_API_URL=http://localhost:8000
   ```

3. **Start development server**:
   ```bash
   npm start
   ```

4. **Open browser**: Navigate to `http://localhost:3000`

### Production Build

```bash
# Build for production
npm run build

# Serve locally (optional)
npm install -g serve
serve -s build -l 3000
```

## Docker Deployment

### Production

```bash
# Build and run production container
docker-compose up -d frontend
```

### Development with Hot Reload

```bash
# Run development container with hot reload
docker-compose --profile dev up frontend-dev
```

## API Configuration

The frontend connects to two APIs:

1. **n8n API** (`https://n8n.unit-y-ai.io/api/v1`)
   - Requires API key authentication
   - Manages workflows, executions, credentials

2. **Playground API** (`http://localhost:8000`)
   - Local FastAPI backend
   - Additional automation features

### Setting up n8n API Key

1. **Generate API Key in n8n**:
   - Go to n8n Settings → API Keys
   - Create new API key
   - Copy the generated key

2. **Configure in Frontend**:
   The API key should be included in requests automatically.
   For production, ensure the key is properly configured in your deployment.

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── Layout.tsx      # Main layout with navigation
│   └── ConnectionStatus.tsx
├── contexts/           # React contexts
│   └── ApiContext.tsx  # API configuration and state
├── pages/              # Page components
│   ├── Dashboard.tsx   # Main dashboard
│   ├── Workflows.tsx   # Workflow management
│   ├── Executions.tsx  # Execution history
│   ├── Credentials.tsx # Credential management
│   ├── Settings.tsx    # System settings
│   ├── WorkflowDetail.tsx
│   └── ExecutionDetail.tsx
├── App.tsx             # Main app component
├── index.tsx           # Entry point
└── index.css           # Global styles
```

## Available Scripts

- `npm start` - Start development server
- `npm run build` - Build for production
- `npm test` - Run tests
- `npm run eject` - Eject from Create React App

## Features Overview

### Dashboard
- System status overview
- Execution statistics
- Recent activity feed
- Quick actions

### Workflow Management
- View all workflows
- Activate/deactivate workflows
- Execute workflows manually
- View workflow details
- Delete workflows

### Execution Monitoring
- View execution history
- Filter by status and workflow
- Detailed execution logs
- Retry failed executions

### Credential Management
- View stored credentials
- Manage API keys and tokens
- Security overview

### Settings
- API configuration
- System information
- Connection status
- Quick links to n8n editor

## Security

- API keys are handled securely
- CORS protection enabled
- Content Security Policy configured
- No sensitive data in localStorage
- Secure headers in nginx configuration

## Troubleshooting

### Common Issues

1. **API Connection Failed**:
   - Check if n8n is running at the configured URL
   - Verify API key is valid
   - Check network connectivity

2. **CORS Errors**:
   - Ensure n8n CORS settings allow your domain
   - Use the nginx proxy configuration provided

3. **Build Errors**:
   - Clear node_modules and reinstall: `rm -rf node_modules package-lock.json && npm install`
   - Check Node.js version compatibility

### Development Tips

- Use React Developer Tools for debugging
- Check browser console for API errors
- Monitor network tab for failed requests
- Use the connection status indicator

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is part of the UnityAI platform. See the main repository for license information.