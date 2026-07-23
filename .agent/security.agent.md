# Security — Sandbox & Execution Guardrails

> **Goal:** JARVIS can execute code and generate tools SAFELY, with human oversight.
> **Est. time:** 3-4 hours · **Cross-cutting:** All tiers (especially Tier 4)

## ✅ Checklist
- [ ] `core/security.py` — Sandbox & permissions system
- [ ] Layer 1: Input validation (sanitize user input)
- [ ] Layer 2: Tool execution sandbox (subprocess isolation)
- [ ] Layer 3: Code generation guard (AST parsing, dangerous pattern detection)
- [ ] Layer 4: User permissions system (granular per-action controls)
- [ ] Static analysis for generated code
- [ ] Resource limits (CPU, memory, timeout)
- [ ] Human-in-the-loop approval workflow
- [ ] Audit logging of all tool executions
- [ ] Rate limiting

---

## 📄 core/security.py

```python
"""
Security Module — Sandbox, permissions, code guardrails, audit logging.

Four layers of security:
1. Input Validation
2. Tool Execution Sandbox
3. Code Generation Guard
4. User Permissions System
"""

import ast
import os
import subprocess
import sys
import time
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from datetime import datetime


# ================================================
# LAYER 4: Permissions System
# ================================================

class PermissionLevel:
    """Permission levels for actions."""
    ALWAYS = "always"        # No confirmation needed
    CONFIRM = "confirm"      # Ask user before each
    DENY = "deny"            # Never allowed
    ONCE = "once"            # Ask once per session, then remember


# Default permissions — override in settings.yaml
DEFAULT_PERMISSIONS = {
    "read_file": PermissionLevel.ALWAYS,
    "write_file": PermissionLevel.CONFIRM,
    "delete_file": PermissionLevel.CONFIRM,
    "execute_python": PermissionLevel.CONFIRM,
    "execute_bash": PermissionLevel.CONFIRM,
    "install_package": PermissionLevel.CONFIRM,
    "access_camera": PermissionLevel.ALWAYS,
    "access_mic": PermissionLevel.ALWAYS,
    "send_email": PermissionLevel.CONFIRM,
    "web_search": PermissionLevel.ALWAYS,
    "control_mouse": PermissionLevel.CONFIRM,
    "control_keyboard": PermissionLevel.CONFIRM,
    "control_hardware": PermissionLevel.CONFIRM,
    "generate_tool": PermissionLevel.CONFIRM,
    "self_improve": PermissionLevel.CONFIRM,
}


@dataclass
class AuditEntry:
    """An audit log entry for a security-relevant action."""
    timestamp: str
    action: str
    permission: str
    approved: bool
    details: str
    user_input: str = ""
    result: str = ""


# ================================================
# LAYER 1: Input Validation
# ================================================

class InputValidator:
    """Validate and sanitize user input before it reaches the LLM."""
    
    @staticmethod
    def sanitize(text: str) -> str:
        """Remove potentially dangerous content from user input."""
        # Remove control characters (except newlines)
        cleaned = "".join(c for c in text if c == '\n' or c == '\t' or (c >= ' ' and c <= '~') or ord(c) > 127)
        return cleaned.strip()
    
    @staticmethod
    def detect_injection(text: str) -> bool:
        """Detect prompt injection attempts."""
        dangerous_patterns = [
            "ignore all previous instructions",
            "forget your previous instructions",
            "you are now",
            "system prompt",
            "you must obey",
            "override",
        ]
        text_lower = text.lower()
        for pattern in dangerous_patterns:
            if pattern in text_lower:
                return True
        return False


# ================================================
# LAYER 2: Tool Execution Sandbox
# ================================================

class Sandbox:
    """Sandboxed execution environment for tools and code."""
    
    def __init__(self, settings):
        self.timeout = settings.get("tools.sandbox_timeout", 30)
        self.max_memory = settings.get("tools.sandbox_max_memory", 500)
        self.allowed_paths = [
            str(Path("./custom_tools").resolve()),
            str(Path("./logs").resolve()),
            str(Path("./memory_store").resolve()),
        ]
        self.audit_log: List[AuditEntry] = []
    
    def execute_python(self, code: str, context: dict = None) -> Dict:
        """
        Execute Python code in a sandboxed subprocess.
        Returns: {"success": bool, "output": str, "error": str}
        """
        # Check for dangerous patterns first
        danger_check = CodeGuard.scan_code(code)
        if danger_check:
            return {
                "success": False,
                "output": "",
                "error": f"Security block: {danger_check}",
            }
        
        # Execute in subprocess with restrictions
        wrapped_code = f"""
import sys, json
sys.path.insert(0, '{Path("./custom_tools").resolve()}')
try:
    result = {code}
    print(json.dumps({{"success": True, "result": str(result)}}))
except Exception as e:
    print(json.dumps({{"success": False, "error": str(e)}}))
"""
        
        try:
            result = subprocess.run(
                [sys.executable, "-c", wrapped_code],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env={
                    "PATH": os.environ.get("PATH", ""),
                    "HOME": os.environ.get("HOME", ""),
                    # No API keys in sandbox
                },
                cwd=str(Path("./custom_tools").resolve()),
            )
            
            if result.returncode == 0:
                try:
                    return json.loads(result.stdout.strip())
                except:
                    return {"success": True, "output": result.stdout}
            else:
                return {
                    "success": False,
                    "output": result.stdout,
                    "error": result.stderr,
                }
        
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Execution timed out ({self.timeout}s)"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def execute_bash(self, command: str) -> Dict:
        """Execute a bash command with restrictions."""
        # Blacklist dangerous commands
        dangerous = ["rm -rf", "mkfs", "dd if=", "> /dev/sd", ":(){ :|:& };:"]
        for d in dangerous:
            if d in command:
                return {"success": False, "error": f"Blocked dangerous command pattern: {d}"}
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env={},
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else "",
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Command timed out ({self.timeout}s)"}
    
    def log_audit(self, entry: AuditEntry):
        """Log a security-relevant action."""
        self.audit_log.append(entry)
        
        log_path = Path("./logs/audit.jsonl")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a") as f:
            f.write(json.dumps(asdict(entry)) + "\n")


# ================================================
# LAYER 3: Code Generation Guard
# ================================================

class CodeGuard:
    """Static analysis and safety checks for generated code."""
    
    # Patterns that are NEVER allowed in generated code
    DANGEROUS_PATTERNS = [
        "__import__",
        "compile(",
        "exec(",
        "eval(",
        "getattr(",
        "setattr(",
        "delattr(",
        "globals()",
        "locals()",
        "vars()",
    ]
    
    # Imports that require special approval
    DANGEROUS_MODULES = {
        "os": ["system", "popen", "fork", "kill", "removedirs"],
        "subprocess": ["run", "Popen", "call", "check_output"],
        "shutil": ["rmtree", "chown", "chmod"],
        "socket": ["socket", "create_connection"],
        "ctypes": ["CDLL", "windll", "cdll"],
    }
    
    @classmethod
    def scan_code(cls, code: str) -> Optional[str]:
        """
        Scan generated code for dangerous patterns.
        Returns None if safe, or an error string describing the issue.
        """
        # Check raw patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            if pattern in code:
                return f"Blocked dangerous pattern: '{pattern}'"
        
        # Parse AST for deeper analysis
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return f"Syntax error in generated code: {e}"
        
        # Walk AST for dangerous imports and calls
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in cls.DANGEROUS_MODULES:
                        return f"Blocked dangerous import: '{alias.name}'"
            
            elif isinstance(node, ast.ImportFrom):
                if node.module in cls.DANGEROUS_MODULES:
                    names = [n.name for n in node.names]
                    dangerous = cls.DANGEROUS_MODULES[node.module]
                    for name in names:
                        if name in dangerous:
                            return f"Blocked dangerous import: '{node.module}.{name}'"
            
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    # Check for dangerous method calls
                    if node.func.attr in ["system", "popen", "rmtree", "kill"]:
                        return f"Blocked dangerous function call: '{node.func.attr}'"
                    
                    # Check for file operations outside allowed paths
                    if node.func.attr in ["open", "write_text", "write_bytes"]:
                        for arg in node.args:
                            if isinstance(arg, ast.Str):
                                path = arg.s
                                # Allow only relative paths or paths in custom_tools
                                if path.startswith("/") and not path.startswith("/tmp/"):
                                    return f"Blocked absolute path: '{path}'"
        
        return None  # Safe
    
    @classmethod
    def get_allowed_imports(cls) -> List[str]:
        """Return list of modules that generated code can import."""
        return [
            "json", "math", "random", "datetime", "time",
            "typing", "collections", "itertools", "functools",
            "re", "string", "pathlib", "os.path",
            "requests", "beautifulsoup4",
            "numpy", "pandas",
            # Add more as needed
        ]


class Security:
    """
    Master security controller.
    Orchestrates all four security layers.
    """
    
    def __init__(self, settings):
        self.permissions = dict(DEFAULT_PERMISSIONS)
        self.sandbox = Sandbox(settings)
        self.validator = InputValidator()
        
        # Override permissions from settings
        custom_perms = settings.get("security.permissions", {})
        for action, level in custom_perms.items():
            if action in self.permissions:
                self.permissions[action] = level
        
        self._session_approvals = set()
    
    def check_permission(self, action: str) -> bool:
        """
        Check if an action is permitted.
        Returns True if action can proceed, False if denied.
        """
        level = self.permissions.get(action, PermissionLevel.CONFIRM)
        
        if level == PermissionLevel.ALWAYS:
            return True
        elif level == PermissionLevel.DENY:
            return False
        elif level == PermissionLevel.ONCE:
            if action in self._session_approvals:
                return True
            approved = self._prompt_user(action)
            if approved:
                self._session_approvals.add(action)
            return approved
        elif level == PermissionLevel.CONFIRM:
            return self._prompt_user(action)
        
        return False
    
    def _prompt_user(self, action: str) -> bool:
        """Prompt the user for permission (terminal-based for now)."""
        print(f"\n🔒 JARVIS needs permission to: {action}")
        response = input("Allow? (y/N): ").strip().lower()
        return response == "y"
    
    def validate_input(self, text: str) -> tuple:
        """
        Validate user input.
        Returns: (is_safe: bool, cleaned_text: str)
        """
        cleaned = InputValidator.sanitize(text)
        is_injection = InputValidator.detect_injection(cleaned)
        
        if is_injection:
            print("⚠️ Potential prompt injection detected!")
            return (False, cleaned)
        
        return (True, cleaned)
    
    def execute_safely(self, action: str, code_or_command: str,
                       tool_name: str = None) -> Dict:
        """
        Execute code/commands through the full security pipeline.
        1. Check permissions
        2. Scan for dangerous patterns
        3. Execute in sandbox
        4. Log to audit
        """
        # Check permission
        if not self.check_permission(action):
            entry = AuditEntry(
                timestamp=datetime.now().isoformat(),
                action=action,
                permission=self.permissions.get(action, "unknown"),
                approved=False,
                details=f"User denied {'tool: ' + tool_name if tool_name else action}",
            )
            self.sandbox.log_audit(entry)
            return {"success": False, "error": f"Permission denied: {action}"}
        
        # Execute based on action type
        result = None
        if action == "execute_python":
            result = self.sandbox.execute_python(code_or_command)
        elif action == "execute_bash":
            result = self.sandbox.execute_bash(code_or_command)
        else:
            result = {"success": False, "error": f"Unknown action: {action}"}
        
        # Log audit
        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            action=action,
            permission=self.permissions.get(action, "unknown"),
            approved=True,
            details=f"{'Tool: ' + tool_name if tool_name else action}",
            result=str(result),
        )
        self.sandbox.log_audit(entry)
        
        return result
```
