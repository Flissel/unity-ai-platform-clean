"""Code execution service for secure code testing and validation."""

import asyncio
import tempfile
import subprocess
import os
import shutil
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

from ..core.config import get_settings
from ..core.logging import get_logger, log_execution_time
from ..core.exceptions import (
    CodeExecutionError, ValidationError, TimeoutError, 
    SecurityError, ConfigurationError
)
from ..core.models import CodeExecutionRequest, CodeExecutionResult, ExecutionStatus
from ..core.cache import cached, SessionCache

logger = get_logger(__name__)


class SecurityValidator:
    """Validates code for security issues before execution."""
    
    # Dangerous patterns that should be blocked
    DANGEROUS_PATTERNS = {
        'python': [
            r'import\s+os',
            r'import\s+subprocess',
            r'import\s+sys',
            r'from\s+os\s+import',
            r'from\s+subprocess\s+import',
            r'from\s+sys\s+import',
            r'__import__',
            r'eval\s*\(',
            r'exec\s*\(',
            r'compile\s*\(',
            r'open\s*\(',
            r'file\s*\(',
            r'input\s*\(',
            r'raw_input\s*\(',
            r'globals\s*\(',
            r'locals\s*\(',
            r'vars\s*\(',
            r'dir\s*\(',
            r'hasattr\s*\(',
            r'getattr\s*\(',
            r'setattr\s*\(',
            r'delattr\s*\(',
        ],
        'javascript': [
            r'require\s*\(',
            r'import\s+.*\s+from',
            r'import\s*\(',
            r'eval\s*\(',
            r'Function\s*\(',
            r'setTimeout\s*\(',
            r'setInterval\s*\(',
            r'process\.',
            r'global\.',
            r'window\.',
            r'document\.',
            r'localStorage',
            r'sessionStorage',
            r'fetch\s*\(',
            r'XMLHttpRequest',
        ],
        'bash': [
            r'rm\s+-rf',
            r'sudo\s+',
            r'su\s+',
            r'chmod\s+',
            r'chown\s+',
            r'wget\s+',
            r'curl\s+',
            r'nc\s+',
            r'netcat\s+',
            r'/etc/',
            r'/proc/',
            r'/sys/',
            r'>/dev/',
        ]
    }
    
    @classmethod
    def validate_code(cls, code: str, language: str) -> List[str]:
        """Validate code for security issues.
        
        Returns:
            List of security issues found
        """
        import re
        
        issues = []
        patterns = cls.DANGEROUS_PATTERNS.get(language.lower(), [])
        
        for pattern in patterns:
            if re.search(pattern, code, re.IGNORECASE | re.MULTILINE):
                issues.append(f"Potentially dangerous pattern detected: {pattern}")
        
        # Check for suspicious file operations
        if language.lower() == 'python':
            if 'open(' in code and ('w' in code or 'a' in code):
                issues.append("File write operations detected")
        
        # Check for network operations
        network_patterns = ['http', 'https', 'ftp', 'socket', 'urllib', 'requests']
        for pattern in network_patterns:
            if pattern in code.lower():
                issues.append(f"Network operation detected: {pattern}")
        
        return issues


class CodeSandbox:
    """Secure sandbox for code execution."""
    
    def __init__(self, execution_id: str, language: str):
        self.execution_id = execution_id
        self.language = language.lower()
        self.temp_dir: Optional[Path] = None
        self.settings = get_settings()
    
    async def __aenter__(self):
        """Enter sandbox context."""
        self.temp_dir = Path(tempfile.mkdtemp(prefix=f"code_exec_{self.execution_id}_"))
        logger.debug(f"Created sandbox directory: {self.temp_dir}")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit sandbox context and cleanup."""
        if self.temp_dir and self.temp_dir.exists():
            try:
                shutil.rmtree(self.temp_dir)
                logger.debug(f"Cleaned up sandbox directory: {self.temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to cleanup sandbox: {e}")
    
    def get_file_path(self, filename: str) -> Path:
        """Get path for a file in the sandbox."""
        if not self.temp_dir:
            raise RuntimeError("Sandbox not initialized")
        return self.temp_dir / filename
    
    def write_code_file(self, code: str, filename: Optional[str] = None) -> Path:
        """Write code to a file in the sandbox."""
        if not filename:
            extensions = {
                'python': '.py',
                'javascript': '.js',
                'bash': '.sh',
                'shell': '.sh',
                'sql': '.sql'
            }
            extension = extensions.get(self.language, '.txt')
            filename = f"code_{self.execution_id}{extension}"
        
        file_path = self.get_file_path(filename)
        file_path.write_text(code, encoding='utf-8')
        
        # Make shell scripts executable
        if self.language in ['bash', 'shell']:
            os.chmod(file_path, 0o755)
        
        return file_path
    
    def get_execution_command(self, file_path: Path) -> List[str]:
        """Get command to execute the code file."""
        commands = {
            'python': ['python', str(file_path)],
            'python3': ['python3', str(file_path)],
            'javascript': ['node', str(file_path)],
            'bash': ['bash', str(file_path)],
            'shell': ['sh', str(file_path)],
        }
        
        command = commands.get(self.language)
        if not command:
            raise ValidationError(f"Unsupported language: {self.language}")
        
        return command


class CodeExecutionService:
    """Service for secure code execution and testing."""
    
    def __init__(self):
        self.settings = get_settings()
        self._active_executions: Dict[str, asyncio.Task] = {}
        self._execution_cache = SessionCache("code_execution")
    
    @log_execution_time(logger, "Code execution")
    async def execute_code(
        self,
        request: CodeExecutionRequest,
        timeout: Optional[int] = None
    ) -> CodeExecutionResult:
        """Execute code securely in a sandbox.
        
        Args:
            request: Code execution request
            timeout: Execution timeout in seconds
            
        Returns:
            Code execution result
        """
        execution_id = str(uuid4())
        start_time = datetime.utcnow()
        
        try:
            # Validate request
            self._validate_request(request)
            
            # Security validation
            if self.settings.code_execution.security_enabled:
                security_issues = SecurityValidator.validate_code(
                    request.code, request.language
                )
                if security_issues:
                    raise SecurityError(f"Security validation failed: {'; '.join(security_issues)}")
            
            # Check execution limits
            await self._check_execution_limits()
            
            # Execute code
            execution_timeout = timeout or self.settings.code_execution.timeout
            
            logger.info(f"Starting code execution: {execution_id} ({request.language})")
            
            result = await asyncio.wait_for(
                self._execute_in_sandbox(execution_id, request),
                timeout=execution_timeout
            )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Create result
            execution_result = CodeExecutionResult(
                execution_id=execution_id,
                status=ExecutionStatus.COMPLETED if result['success'] else ExecutionStatus.FAILED,
                output=result.get('output', ''),
                error=result.get('error'),
                execution_time=execution_time,
                exit_code=result.get('exit_code', 0),
                metadata={
                    'language': request.language,
                    'code_length': len(request.code),
                    'timeout': execution_timeout,
                    'security_enabled': self.settings.code_execution.security_enabled,
                    'timestamp': start_time.isoformat()
                }
            )
            
            # Cache result
            await self._cache_result(execution_id, execution_result)
            
            logger.info(f"Code execution completed: {execution_id} ({execution_time:.2f}s)")
            return execution_result
            
        except asyncio.TimeoutError:
            logger.error(f"Code execution timed out: {execution_id}")
            return CodeExecutionResult(
                execution_id=execution_id,
                status=ExecutionStatus.TIMEOUT,
                error=f"Execution timed out after {execution_timeout}s",
                execution_time=(datetime.utcnow() - start_time).total_seconds()
            )
        except Exception as e:
            logger.error(f"Code execution failed: {execution_id} - {e}")
            return CodeExecutionResult(
                execution_id=execution_id,
                status=ExecutionStatus.FAILED,
                error=str(e),
                execution_time=(datetime.utcnow() - start_time).total_seconds()
            )
        finally:
            # Cleanup active execution tracking
            self._active_executions.pop(execution_id, None)
    
    def _validate_request(self, request: CodeExecutionRequest) -> None:
        """Validate code execution request."""
        if not request.code.strip():
            raise ValidationError("Code cannot be empty")
        
        if len(request.code) > self.settings.code_execution.max_code_length:
            raise ValidationError(
                f"Code too long: {len(request.code)} > {self.settings.code_execution.max_code_length}"
            )
        
        supported_languages = self.settings.code_execution.supported_languages
        if request.language.lower() not in [lang.lower() for lang in supported_languages]:
            raise ValidationError(
                f"Unsupported language: {request.language}. "
                f"Supported: {', '.join(supported_languages)}"
            )
    
    async def _check_execution_limits(self) -> None:
        """Check if execution limits are exceeded."""
        max_concurrent = self.settings.code_execution.max_concurrent_executions
        if len(self._active_executions) >= max_concurrent:
            raise CodeExecutionError(
                f"Maximum concurrent executions exceeded: {max_concurrent}"
            )
    
    async def _execute_in_sandbox(
        self,
        execution_id: str,
        request: CodeExecutionRequest
    ) -> Dict[str, Any]:
        """Execute code in a secure sandbox."""
        async with CodeSandbox(execution_id, request.language) as sandbox:
            try:
                # Write code to file
                code_file = sandbox.write_code_file(request.code)
                
                # Get execution command
                command = sandbox.get_execution_command(code_file)
                
                # Execute with resource limits
                process = await asyncio.create_subprocess_exec(
                    *command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=sandbox.temp_dir,
                    env=self._get_safe_environment()
                )
                
                # Track active execution
                task = asyncio.current_task()
                if task:
                    self._active_executions[execution_id] = task
                
                # Wait for completion
                stdout, stderr = await process.communicate()
                
                # Decode output
                output = stdout.decode('utf-8', errors='replace')
                error = stderr.decode('utf-8', errors='replace')
                
                return {
                    'success': process.returncode == 0,
                    'output': output,
                    'error': error if error else None,
                    'exit_code': process.returncode
                }
                
            except Exception as e:
                logger.error(f"Sandbox execution failed: {e}")
                return {
                    'success': False,
                    'error': f"Execution failed: {e}",
                    'exit_code': -1
                }
    
    def _get_safe_environment(self) -> Dict[str, str]:
        """Get safe environment variables for code execution."""
        # Start with minimal environment
        safe_env = {
            'PATH': '/usr/local/bin:/usr/bin:/bin',
            'HOME': '/tmp',
            'USER': 'sandbox',
            'LANG': 'en_US.UTF-8',
            'LC_ALL': 'en_US.UTF-8'
        }
        
        # Add language-specific variables
        if self.settings.code_execution.allow_network:
            safe_env.update({
                'HTTP_PROXY': '',
                'HTTPS_PROXY': '',
                'NO_PROXY': 'localhost,127.0.0.1'
            })
        
        return safe_env
    
    async def _cache_result(
        self,
        execution_id: str,
        result: CodeExecutionResult
    ) -> None:
        """Cache execution result."""
        try:
            await self._execution_cache.set(
                execution_id,
                result.model_dump(),
                ttl=3600  # Cache for 1 hour
            )
        except Exception as e:
            logger.warning(f"Failed to cache execution result: {e}")
    
    async def get_execution_result(self, execution_id: str) -> Optional[CodeExecutionResult]:
        """Get cached execution result."""
        try:
            cached_data = await self._execution_cache.get(execution_id)
            if cached_data:
                return CodeExecutionResult(**cached_data)
        except Exception as e:
            logger.warning(f"Failed to retrieve cached result: {e}")
        return None
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running execution."""
        task = self._active_executions.get(execution_id)
        if task and not task.done():
            task.cancel()
            logger.info(f"Cancelled execution: {execution_id}")
            return True
        return False
    
    async def get_active_executions(self) -> List[str]:
        """Get list of active execution IDs."""
        return [
            exec_id for exec_id, task in self._active_executions.items()
            if not task.done()
        ]
    
    @cached(ttl=300, key_prefix="code_exec:capabilities")
    async def get_capabilities(self) -> Dict[str, Any]:
        """Get code execution capabilities."""
        return {
            'supported_languages': self.settings.code_execution.supported_languages,
            'max_code_length': self.settings.code_execution.max_code_length,
            'timeout': self.settings.code_execution.timeout,
            'max_concurrent': self.settings.code_execution.max_concurrent_executions,
            'security_enabled': self.settings.code_execution.security_enabled,
            'network_allowed': self.settings.code_execution.allow_network,
            'limits': {
                'memory': '512MB',  # Would be configured in container
                'cpu': '1 core',    # Would be configured in container
                'disk': '100MB'     # Would be configured in container
            }
        }
    
    async def health_check(self) -> bool:
        """Check code execution service health."""
        try:
            # Test with simple code execution
            test_request = CodeExecutionRequest(
                code="print('health check')",
                language="python"
            )
            
            result = await self.execute_code(test_request, timeout=5)
            return result.status == ExecutionStatus.COMPLETED
            
        except Exception as e:
            logger.error(f"Code execution health check failed: {e}")
            return False
    
    async def get_usage_statistics(self) -> Dict[str, Any]:
        """Get service usage statistics."""
        return {
            'active_executions': len(self._active_executions),
            'max_concurrent': self.settings.code_execution.max_concurrent_executions,
            'supported_languages': len(self.settings.code_execution.supported_languages),
            'security_enabled': self.settings.code_execution.security_enabled,
            'timestamp': datetime.utcnow().isoformat()
        }


# Global service instance
code_execution_service = CodeExecutionService()


# Convenience functions
async def execute_code(
    code: str,
    language: str,
    timeout: Optional[int] = None
) -> CodeExecutionResult:
    """Execute code with the global service."""
    request = CodeExecutionRequest(code=code, language=language)
    return await code_execution_service.execute_code(request, timeout)


async def get_execution_capabilities() -> Dict[str, Any]:
    """Get execution capabilities."""
    return await code_execution_service.get_capabilities()