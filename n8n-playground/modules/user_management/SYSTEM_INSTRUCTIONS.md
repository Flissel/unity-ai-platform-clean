# User Management Module - System Instructions

## Module Overview

**Purpose**: Comprehensive user management system for the n8n API Playground integration, providing authentication, authorization, user lifecycle management, and integration with existing UnityAI user systems.

**Module Name**: `user_management`  
**Version**: 1.0.0  
**Author**: UnityAI Team  
**Dependencies**: FastAPI, SQLAlchemy, Pydantic, bcrypt, JWT, Redis, structlog

## Core Responsibilities

### 1. Authentication
- **User Authentication**: Secure login/logout functionality
- **Token Management**: JWT token generation, validation, and refresh
- **Multi-Factor Authentication**: Optional MFA support
- **Session Management**: User session tracking and management

### 2. Authorization
- **Role-Based Access Control (RBAC)**: Define and manage user roles
- **Permission Management**: Granular permission system
- **Resource Access Control**: Control access to workflows and resources
- **API Access Control**: Secure API endpoint access

### 3. User Lifecycle
- **User Registration**: New user registration and onboarding
- **Profile Management**: User profile updates and preferences
- **Account Management**: Account activation, deactivation, deletion
- **Password Management**: Password reset, change, and policies

### 4. Integration
- **UnityAI Integration**: Seamless integration with existing user system
- **n8n Integration**: User mapping and workflow ownership
- **External Providers**: OAuth integration (Google, GitHub, etc.)
- **API Integration**: RESTful API for user management operations

## File Structure

```
modules/user_management/
├── SYSTEM_INSTRUCTIONS.md     # This file
├── __init__.py                # Module exports
├── auth_manager.py            # Authentication management
├── user_manager.py            # User lifecycle management
├── role_manager.py            # Role and permission management
├── session_manager.py         # Session management
├── password_manager.py        # Password management
├── oauth_manager.py           # OAuth integration
├── integration_manager.py     # External system integration
├── models.py                  # Pydantic and SQLAlchemy models
├── api.py                     # FastAPI endpoints
├── config.py                  # Module configuration
├── exceptions.py              # Custom exceptions
├── utils.py                   # Utility functions
├── middleware.py              # Authentication middleware
├── decorators.py              # Authorization decorators
├── validators.py              # Input validation
├── schemas/
│   ├── __init__.py
│   ├── user_schemas.py        # User-related schemas
│   ├── auth_schemas.py        # Authentication schemas
│   ├── role_schemas.py        # Role and permission schemas
│   └── integration_schemas.py # Integration schemas
├── database/
│   ├── __init__.py
│   ├── models.py              # SQLAlchemy models
│   ├── migrations/            # Database migrations
│   └── seeds/                 # Database seed data
├── providers/
│   ├── __init__.py
│   ├── google_oauth.py        # Google OAuth provider
│   ├── github_oauth.py        # GitHub OAuth provider
│   ├── microsoft_oauth.py     # Microsoft OAuth provider
│   └── custom_oauth.py        # Custom OAuth provider
├── policies/
│   ├── __init__.py
│   ├── password_policy.py     # Password policy enforcement
│   ├── access_policy.py       # Access control policies
│   └── security_policy.py     # Security policies
├── tests/
│   ├── __init__.py
│   ├── test_auth_manager.py
│   ├── test_user_manager.py
│   ├── test_role_manager.py
│   ├── test_oauth_manager.py
│   └── test_integration.py
└── docs/
    ├── api_reference.md
    ├── authentication_guide.md
    ├── authorization_guide.md
    ├── integration_guide.md
    └── security_guide.md
```

## Implementation Guidelines

### 1. Code Standards
- **Python Version**: 3.9+
- **Type Hints**: Mandatory for all functions and methods
- **Docstrings**: Google-style docstrings for all public methods
- **Error Handling**: Comprehensive error handling with structured logging
- **Async/Await**: Use async/await for all I/O operations

### 2. Data Models
- **Pydantic Models**: Use Pydantic for API data validation
- **SQLAlchemy Models**: Use SQLAlchemy for database models
- **Data Validation**: Strict input validation and sanitization
- **Schema Versioning**: Support for API schema versioning

### 3. Security Standards
- **Password Hashing**: Use bcrypt for password hashing
- **JWT Security**: Secure JWT implementation with proper claims
- **Input Sanitization**: Sanitize all user inputs
- **SQL Injection Prevention**: Use parameterized queries

### 4. Testing Requirements
- **Unit Tests**: 95%+ code coverage
- **Integration Tests**: Test with real authentication flows
- **Security Tests**: Test for common security vulnerabilities
- **Performance Tests**: Test authentication performance

## Authentication Manager Specifications

### Core Components

#### 1. AuthManager Class
```python
class AuthManager:
    """Main authentication management system."""
    
    async def authenticate_user(self, credentials: UserCredentials) -> AuthResult
    async def generate_tokens(self, user: User) -> TokenPair
    async def validate_token(self, token: str) -> TokenValidation
    async def refresh_token(self, refresh_token: str) -> TokenPair
    async def logout_user(self, user_id: str, token: str) -> bool
    async def enable_mfa(self, user_id: str, method: MFAMethod) -> MFASetup
    async def verify_mfa(self, user_id: str, code: str) -> bool
```

#### 2. Authentication Models
```python
class UserCredentials(BaseModel):
    username: str
    password: str
    mfa_code: Optional[str]
    remember_me: bool = False

class AuthResult(BaseModel):
    success: bool
    user: Optional[User]
    tokens: Optional[TokenPair]
    mfa_required: bool = False
    error_message: Optional[str]

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
```

### Authentication Methods
- **Username/Password**: Traditional username and password authentication
- **Email/Password**: Email-based authentication
- **OAuth**: Third-party OAuth providers (Google, GitHub, Microsoft)
- **API Key**: API key-based authentication for programmatic access
- **Multi-Factor Authentication**: TOTP, SMS, email-based MFA

## User Manager Specifications

### Core Components

#### 1. UserManager Class
```python
class UserManager:
    """User lifecycle management system."""
    
    async def create_user(self, user_data: UserCreate) -> User
    async def get_user(self, user_id: str) -> Optional[User]
    async def update_user(self, user_id: str, user_data: UserUpdate) -> User
    async def delete_user(self, user_id: str) -> bool
    async def activate_user(self, user_id: str) -> bool
    async def deactivate_user(self, user_id: str) -> bool
    async def list_users(self, filters: UserFilters) -> List[User]
    async def search_users(self, query: str) -> List[User]
```

#### 2. User Models
```python
class User(BaseModel):
    id: str
    username: str
    email: str
    first_name: str
    last_name: str
    is_active: bool = True
    is_verified: bool = False
    roles: List[Role] = []
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    preferences: Dict[str, Any] = {}

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    roles: List[str] = []

class UserUpdate(BaseModel):
    email: Optional[EmailStr]
    first_name: Optional[str]
    last_name: Optional[str]
    preferences: Optional[Dict[str, Any]]
```

### User Operations
- **Registration**: User self-registration with email verification
- **Profile Management**: Update profile information and preferences
- **Account Status**: Activate, deactivate, suspend user accounts
- **Bulk Operations**: Bulk user creation, updates, and deletions

## Role Manager Specifications

### Core Components

#### 1. RoleManager Class
```python
class RoleManager:
    """Role and permission management system."""
    
    async def create_role(self, role_data: RoleCreate) -> Role
    async def get_role(self, role_id: str) -> Optional[Role]
    async def update_role(self, role_id: str, role_data: RoleUpdate) -> Role
    async def delete_role(self, role_id: str) -> bool
    async def assign_role(self, user_id: str, role_id: str) -> bool
    async def revoke_role(self, user_id: str, role_id: str) -> bool
    async def check_permission(self, user_id: str, permission: str) -> bool
    async def list_user_permissions(self, user_id: str) -> List[Permission]
```

#### 2. Role Models
```python
class Role(BaseModel):
    id: str
    name: str
    description: str
    permissions: List[Permission]
    is_system_role: bool = False
    created_at: datetime
    updated_at: datetime

class Permission(BaseModel):
    id: str
    name: str
    description: str
    resource: str
    action: str
    conditions: Optional[Dict[str, Any]]

class RoleCreate(BaseModel):
    name: str
    description: str
    permissions: List[str]
```

### Permission System
- **Resource-Based Permissions**: Permissions tied to specific resources
- **Action-Based Permissions**: Permissions for specific actions (read, write, delete)
- **Conditional Permissions**: Permissions with conditions (time-based, IP-based)
- **Hierarchical Roles**: Support for role inheritance

### Default Roles
- **Super Admin**: Full system access
- **Admin**: Administrative access to user management
- **Workflow Manager**: Manage workflows and executions
- **Developer**: Create and edit workflows
- **Viewer**: Read-only access to workflows
- **Guest**: Limited access to public resources

## Session Manager Specifications

### Core Components

#### 1. SessionManager Class
```python
class SessionManager:
    """User session management system."""
    
    async def create_session(self, user_id: str, session_data: SessionData) -> Session
    async def get_session(self, session_id: str) -> Optional[Session]
    async def update_session(self, session_id: str, data: Dict[str, Any]) -> Session
    async def delete_session(self, session_id: str) -> bool
    async def list_user_sessions(self, user_id: str) -> List[Session]
    async def cleanup_expired_sessions(self) -> int
```

#### 2. Session Models
```python
class Session(BaseModel):
    id: str
    user_id: str
    ip_address: str
    user_agent: str
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    is_active: bool = True
    data: Dict[str, Any] = {}

class SessionData(BaseModel):
    ip_address: str
    user_agent: str
    expires_in: int = 3600  # seconds
    data: Dict[str, Any] = {}
```

### Session Features
- **Session Tracking**: Track user sessions across devices
- **Session Expiration**: Automatic session expiration
- **Session Cleanup**: Cleanup expired sessions
- **Concurrent Sessions**: Support for multiple concurrent sessions
- **Session Security**: Detect suspicious session activity

## OAuth Manager Specifications

### Core Components

#### 1. OAuthManager Class
```python
class OAuthManager:
    """OAuth integration management."""
    
    async def get_authorization_url(self, provider: str, state: str) -> str
    async def exchange_code(self, provider: str, code: str, state: str) -> OAuthResult
    async def link_account(self, user_id: str, provider: str, oauth_data: OAuthData) -> bool
    async def unlink_account(self, user_id: str, provider: str) -> bool
    async def refresh_oauth_token(self, user_id: str, provider: str) -> OAuthTokens
```

#### 2. OAuth Models
```python
class OAuthResult(BaseModel):
    success: bool
    user: Optional[User]
    tokens: Optional[TokenPair]
    is_new_user: bool = False
    oauth_data: Optional[OAuthData]

class OAuthData(BaseModel):
    provider: str
    provider_user_id: str
    email: str
    name: str
    avatar_url: Optional[str]
    access_token: str
    refresh_token: Optional[str]
    expires_at: Optional[datetime]
```

### Supported Providers
- **Google**: Google OAuth 2.0 integration
- **GitHub**: GitHub OAuth integration
- **Microsoft**: Microsoft Azure AD integration
- **Custom**: Support for custom OAuth providers

## API Endpoints

### Authentication Endpoints
```
POST   /user-management/auth/login            # User login
POST   /user-management/auth/logout           # User logout
POST   /user-management/auth/refresh          # Refresh token
POST   /user-management/auth/forgot-password  # Forgot password
POST   /user-management/auth/reset-password   # Reset password
POST   /user-management/auth/verify-email     # Verify email
```

### User Management Endpoints
```
POST   /user-management/users                 # Create user
GET    /user-management/users                 # List users
GET    /user-management/users/{id}            # Get user
PUT    /user-management/users/{id}            # Update user
DELETE /user-management/users/{id}            # Delete user
POST   /user-management/users/{id}/activate   # Activate user
POST   /user-management/users/{id}/deactivate # Deactivate user
```

### Role Management Endpoints
```
POST   /user-management/roles                 # Create role
GET    /user-management/roles                 # List roles
GET    /user-management/roles/{id}            # Get role
PUT    /user-management/roles/{id}            # Update role
DELETE /user-management/roles/{id}            # Delete role
POST   /user-management/users/{id}/roles      # Assign role
DELETE /user-management/users/{id}/roles/{role_id} # Revoke role
```

### OAuth Endpoints
```
GET    /user-management/oauth/{provider}/authorize # Get authorization URL
POST   /user-management/oauth/{provider}/callback  # OAuth callback
POST   /user-management/oauth/{provider}/link      # Link OAuth account
DELETE /user-management/oauth/{provider}/unlink   # Unlink OAuth account
```

## Configuration

### Environment Variables
```bash
# User Management Configuration
USER_MANAGEMENT_ENABLED=true
USER_REGISTRATION_ENABLED=true
EMAIL_VERIFICATION_REQUIRED=true
MFA_ENABLED=false

# JWT Configuration
JWT_SECRET_KEY=your_jwt_secret_key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Password Policy
PASSWORD_MIN_LENGTH=8
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_NUMBERS=true
PASSWORD_REQUIRE_SPECIAL=true

# OAuth Configuration
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_email_password

# Database Configuration
USER_DB_URL=postgresql://user:pass@localhost/users
```

### Module Configuration
```python
class UserManagementConfig(BaseModel):
    enabled: bool = True
    registration_enabled: bool = True
    email_verification_required: bool = True
    mfa_enabled: bool = False
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    password_policy: PasswordPolicy
    oauth_providers: Dict[str, OAuthProviderConfig]
    smtp_config: SMTPConfig
    database_url: str
    redis_url: str
```

## Security Considerations

### 1. Authentication Security
- **Password Hashing**: Use bcrypt with appropriate cost factor
- **JWT Security**: Secure JWT implementation with proper claims
- **Token Rotation**: Regular token rotation and revocation
- **Brute Force Protection**: Rate limiting and account lockout

### 2. Authorization Security
- **Principle of Least Privilege**: Grant minimum required permissions
- **Permission Validation**: Validate permissions on every request
- **Role Separation**: Separate administrative and user roles
- **Audit Logging**: Log all authorization decisions

### 3. Data Protection
- **Data Encryption**: Encrypt sensitive data at rest and in transit
- **PII Protection**: Protect personally identifiable information
- **Data Minimization**: Collect only necessary user data
- **Data Retention**: Implement data retention policies

### 4. Session Security
- **Session Fixation Protection**: Regenerate session IDs
- **Session Hijacking Protection**: Validate session integrity
- **Secure Cookies**: Use secure and httpOnly cookies
- **Session Timeout**: Implement appropriate session timeouts

## Performance Requirements

### 1. Authentication Performance
- **Login Time**: < 500ms for standard login
- **Token Validation**: < 50ms for token validation
- **Password Hashing**: < 200ms for password verification

### 2. User Management Performance
- **User Lookup**: < 100ms for user retrieval
- **User Creation**: < 1s for user registration
- **Permission Check**: < 10ms for permission validation

### 3. Scalability
- **Concurrent Users**: Support 10,000+ concurrent users
- **Database Performance**: Efficient database queries
- **Caching**: Redis caching for frequently accessed data

## Monitoring and Observability

### 1. Authentication Metrics
- **Login Success Rate**: Track successful vs failed logins
- **Token Usage**: Monitor token generation and validation
- **MFA Usage**: Track MFA adoption and success rates
- **OAuth Usage**: Monitor OAuth provider usage

### 2. User Metrics
- **User Registration**: Track new user registrations
- **User Activity**: Monitor user activity patterns
- **Role Usage**: Track role assignment and usage
- **Permission Usage**: Monitor permission checks

### 3. Security Metrics
- **Failed Login Attempts**: Track brute force attempts
- **Suspicious Activity**: Detect unusual access patterns
- **Security Events**: Log security-related events
- **Compliance Metrics**: Track compliance requirements

## Development Workflow

### 1. Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Setup database
alembic upgrade head

# Seed initial data
python scripts/seed_data.py

# Run tests
pytest tests/
```

### 2. Testing
```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Security tests
pytest tests/security/

# Coverage report
pytest --cov=modules/user_management
```

### 3. Deployment
```bash
# Run migrations
alembic upgrade head

# Deploy application
docker-compose up -d

# Verify deployment
curl http://localhost:8000/user-management/health
```

## Troubleshooting Guide

### Common Issues

#### 1. Authentication Issues
- **Symptoms**: Login failures, token errors
- **Causes**: Invalid credentials, expired tokens
- **Solutions**: Verify credentials, refresh tokens

#### 2. Authorization Issues
- **Symptoms**: Access denied, permission errors
- **Causes**: Insufficient permissions, role issues
- **Solutions**: Check user roles, verify permissions

#### 3. OAuth Issues
- **Symptoms**: OAuth login failures, callback errors
- **Causes**: Invalid OAuth configuration, network issues
- **Solutions**: Verify OAuth settings, check network

#### 4. Performance Issues
- **Symptoms**: Slow authentication, high latency
- **Causes**: Database performance, network latency
- **Solutions**: Optimize queries, implement caching

### Debugging
- **Enable Debug Logging**: Set log level to DEBUG
- **Check Authentication Flow**: Trace authentication steps
- **Verify Database**: Check database connectivity
- **Monitor Performance**: Use performance profiling

## Future Enhancements

### Phase 1 (Current)
- Basic authentication and authorization
- User lifecycle management
- OAuth integration
- Role-based access control

### Phase 2 (Next)
- Advanced MFA options
- Single Sign-On (SSO)
- Advanced audit logging
- User analytics

### Phase 3 (Future)
- AI-powered security
- Behavioral authentication
- Advanced compliance features
- Identity federation

## Success Criteria

### Functional Requirements
- ✅ Secure authentication system
- ✅ Comprehensive authorization
- ✅ User lifecycle management
- ✅ OAuth integration
- ✅ Role and permission management

### Non-Functional Requirements
- ✅ High security standards
- ✅ Performance requirements met
- ✅ Scalability requirements satisfied
- ✅ High availability (99.9% uptime)
- ✅ Compliance requirements met

### Quality Requirements
- ✅ Code coverage > 95%
- ✅ All security tests passing
- ✅ Documentation complete
- ✅ Security audit passed
- ✅ Performance benchmarks met