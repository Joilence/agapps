import os
import json
from pathlib import Path
from typing import List, Union, Dict

from agapps.schema import AgentApp, MCP, Rule


class ClaudeCode(AgentApp):
    def __init__(self):
        super().__init__(name="Claude Code")
        self.config_paths = {
            "darwin": Path.home()
            / "Library"
            / "Application Support"
            / "Claude"
            / "claude_desktop_config.json",
            "windows": Path(os.environ.get("APPDATA", ""))
            / "Claude"
            / "claude_desktop_config.json",
            "linux": Path.home() / ".config" / "Claude" / "claude_desktop_config.json",
        }
        # Settings and memory files
        self.settings_path = Path.home() / ".claude" / "settings.json"  # Settings file, not rules
        self.global_memory_path = Path.home() / ".claude" / "CLAUDE.md"  # Global memory/rules

    def get_config_path(self) -> Path:
        """Get the platform-specific path to the Claude config file."""
        platform = os.uname().sysname.lower()
        if "darwin" in platform:
            return self.config_paths["darwin"]
        elif "windows" in platform:
            return self.config_paths["windows"]
        elif "linux" in platform:
            return self.config_paths["linux"]
        else:
            raise ValueError(f"Unsupported platform: {platform}")

    def read_config(self) -> Dict:
        """Read the Claude config file if it exists."""
        config_path = self.get_config_path()
        if not config_path.exists():
            return {}

        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def get_mcps(self) -> List[MCP]:
        """
        Get MCP configurations from Claude desktop config.

        The config file has a "mcpServers" key with an array of server specifications.
        Each spec includes name, command, args, env, cwd, etc.
        """
        config = self.read_config()
        mcp_servers = config.get("mcpServers", {})
        result = []

        for server_name, server_details in mcp_servers.items():
            if not isinstance(server_details, dict):
                continue

            name = server_name
            command_executable = server_details.get("command", "")
            args = server_details.get("args", [])
            env_vars = server_details.get("env", {})

            full_command = command_executable
            # Ensure args is a list and not empty; also handle if args is a single string
            if isinstance(args, list) and args:
                full_command = f"{command_executable} {' '.join(args)}".strip()
            elif isinstance(args, str) and args: # Handle case where args might be a single string
                 full_command = f"{command_executable} {args}".strip()
            
            if command_executable:  # Only add if there's a base command executable
                result.append(MCP(name=name, command=full_command, envs=env_vars))
        return result

    def get_mcp_config_paths(self) -> List[Path]:
        """Get the path to the Claude desktop config file if MCPs are present."""
        config_path = self.get_config_path()
        if config_path.exists():
            config = self.read_config()
            if config.get("mcpServers"):
                return [config_path]
        return []

    def get_global_rules(self) -> List[Rule]:
        """
        Get global rules/memory for Claude Code.

        Global memory is defined in:
        - ~/.claude/CLAUDE.md (User memory - personal preferences for all projects)
        
        Note: ~/.claude/settings.json is a settings file, not a rules file
        """
        rules = []

        # Check for global memory file (User memory)
        if self.global_memory_path.exists():
            rules.append(Rule(pattern=self.global_memory_path))

        return rules

    def get_workspace_rules(self, workspace: Union[Path, str]) -> List[Rule]:
        """
        Get workspace-level rules for Claude Code.

        Workspace rules/memory can be defined in:
        - CLAUDE.md (Project memory - team-shared instructions)
        - CLAUDE.local.md (Project memory local - personal project-specific preferences, deprecated)
        
        Settings files (not rules):
        - .claude/settings.json (shared settings)
        - .claude/settings.local.json (local project settings)
        """
        rules = []

        # Convert workspace to Path if it's a string
        if isinstance(workspace, str):
            workspace = Path(workspace)

        # Check for Project memory (team-shared instructions)
        project_memory_path = workspace / "CLAUDE.md"
        if project_memory_path.exists():
            rules.append(Rule(pattern=project_memory_path))

        # Check for Project memory local (personal project-specific preferences, deprecated)
        project_memory_local_path = workspace / "CLAUDE.local.md"
        if project_memory_local_path.exists():
            rules.append(Rule(pattern=project_memory_local_path))

        return rules 