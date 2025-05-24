import json
import os
from pathlib import Path
from typing import Dict, List, Union

from agapps.schema import AgentApp, MCP, Rule


class GitHubCopilot(AgentApp):
    def __init__(self):
        super().__init__(name="GitHub Copilot")
        self.vscode_settings_paths = {
            "darwin": Path.home() / "Library" / "Application Support" / "Code" / "User" / "settings.json",
            "windows": Path(os.environ.get("APPDATA", "")) / "Code" / "User" / "settings.json",
            "linux": Path.home() / ".config" / "Code" / "User" / "settings.json",
        }

    def get_vscode_settings_path(self) -> Path:
        """Get the platform-specific path to VS Code user settings."""
        platform = os.uname().sysname.lower()
        if "darwin" in platform:
            return self.vscode_settings_paths["darwin"]
        elif "windows" in platform:
            return self.vscode_settings_paths["windows"]
        elif "linux" in platform:
            return self.vscode_settings_paths["linux"]
        else:
            # Default to Linux path for unknown platforms
            return self.vscode_settings_paths["linux"]

    def _parse_mcp_server(self, name: str, server_config: Dict) -> MCP:
        """Parse a single MCP server configuration into an MCP object."""
        if not isinstance(server_config, dict):
            return MCP(name=name, command="", envs={})

        command = server_config.get("command", "")
        args = server_config.get("args", [])
        envs = server_config.get("env", {})

        # Build full command with arguments
        full_cmd = command
        if isinstance(args, list) and args:
            full_cmd = f"{command} {' '.join(str(arg) for arg in args)}".strip()
        elif isinstance(args, str) and args:
            full_cmd = f"{command} {args}".strip()

        # Handle HTTP/SSE servers
        if not full_cmd and "url" in server_config:
            url = server_config["url"]
            server_type = server_config.get("type", "")
            if server_type == "sse":
                full_cmd = f"SSE Server: {url}"
            else:
                full_cmd = url

        return MCP(name=name, command=full_cmd, envs=envs if isinstance(envs, dict) else {})

    def _load_json_config(self, config_path: Path) -> Dict:
        """Safely load and parse JSON configuration file."""
        if not config_path.exists():
            return {}

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError, UnicodeDecodeError):
            return {}

    def _extract_mcps_from_workspace_config(self, config: Dict) -> List[MCP]:
        """Extract MCP servers from .vscode/mcp.json configuration."""
        result = []
        
        # GitHub Copilot workspace config has structure: { "inputs": [...], "servers": {...} }
        servers = config.get("servers", {})

        if not isinstance(servers, dict):
            return result

        for name, server_config in servers.items():
            if isinstance(server_config, dict):
                mcp = self._parse_mcp_server(name, server_config)
                if mcp.command:  # Only add servers with valid commands
                    result.append(mcp)

        return result

    def _has_mcp_discovery_enabled(self, config: Dict) -> bool:
        """Check if MCP discovery is enabled in VS Code settings."""
        return config.get("chat.mcp.discovery.enabled", False)

    def get_mcps(self, workspace: Union[Path, str, None] = None) -> List[MCP]:
        """
        Get MCP configurations for GitHub Copilot.
        
        Detects MCP servers from:
        1. Workspace-level: .vscode/mcp.json (GitHub Copilot specific format)
        2. User-level: VS Code settings with MCP discovery enabled (discovers from Claude Desktop etc.)
        """
        result = []

        # Workspace-level MCP config (.vscode/mcp.json)
        workspace_config = Path(".vscode") / "mcp.json"
        if workspace_config.exists():
            config = self._load_json_config(workspace_config)
            result.extend(self._extract_mcps_from_workspace_config(config))

        # User-level VS Code settings (mainly for MCP discovery)
        user_settings = self.get_vscode_settings_path()
        if user_settings.exists():
            config = self._load_json_config(user_settings)
            # GitHub Copilot primarily uses MCP discovery to find existing configurations
            # from other tools like Claude Desktop rather than direct configuration
            if self._has_mcp_discovery_enabled(config):
                # When discovery is enabled, GitHub Copilot automatically finds MCP configs
                # from Claude Desktop and other sources. We can't easily parse those here
                # without duplicating the discovery logic from those other agents.
                pass

        return result

    def get_mcp_config_paths(self) -> List[Path]:
        """
        Get MCP config file paths used by GitHub Copilot.
        
        Returns paths that exist and contain MCP server configurations.
        """
        paths = []

        # Check workspace config
        workspace_config = Path(".vscode") / "mcp.json"
        if workspace_config.exists():
            config = self._load_json_config(workspace_config)
            if config.get("servers"):
                paths.append(workspace_config)

        # Check user settings for MCP discovery
        user_settings = self.get_vscode_settings_path()
        if user_settings.exists():
            config = self._load_json_config(user_settings)
            if self._has_mcp_discovery_enabled(config):
                paths.append(user_settings)

        return paths

    def get_global_rules(self) -> List[Rule]:
        """
        Get global rules for GitHub Copilot.
        
        GitHub Copilot does not support global rules/instructions.
        All customization is done at the repository level via .github/copilot-instructions.md.
        """
        return []

    def get_workspace_rules(self, workspace: Union[Path, str]) -> List[Rule]:
        """
        Get workspace-level rules for GitHub Copilot.

        GitHub Copilot supports repository custom instructions via:
        - .github/copilot-instructions.md
        """
        rules = []
        
        if isinstance(workspace, str):
            workspace = Path(workspace)

        # Check for GitHub Copilot instructions
        instructions_file = workspace / ".github" / "copilot-instructions.md"
        if instructions_file.exists() and instructions_file.is_file():
            rules.append(Rule(pattern=instructions_file))

        return rules