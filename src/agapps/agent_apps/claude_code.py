import os
import json
from pathlib import Path
from typing import List, Union, Dict

from agapps.schema import AgentApp, MCP, Rule


class ClaudeCode(AgentApp):
    def __init__(self):
        super().__init__(name="Claude Code")
        self.global_memory_path = Path.home() / ".claude" / "CLAUDE.md"

    def get_mcps(self, workspace: Union[Path, str, None] = None) -> List[MCP]:
        """
        Get MCP configurations for Claude Code from .mcp.json files.
        """
        if not workspace:
            return []
            
        if isinstance(workspace, str):
            workspace = Path(workspace)
            
        mcp_json_path = workspace / ".mcp.json"
        if not mcp_json_path.exists():
            return []
            
        try:
            with open(mcp_json_path, "r") as f:
                config = json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
            
        result = []
        mcp_servers = config.get("mcpServers", {})
        
        for server_name, server_details in mcp_servers.items():
            if not isinstance(server_details, dict):
                continue
                
            command_executable = server_details.get("command", "")
            args = server_details.get("args", [])
            env_vars = server_details.get("env", {})
            
            full_command = command_executable
            if isinstance(args, list) and args:
                full_command = f"{command_executable} {' '.join(args)}".strip()
            elif isinstance(args, str) and args:
                full_command = f"{command_executable} {args}".strip()
                
            if command_executable:
                result.append(MCP(name=server_name, command=full_command, envs=env_vars))
                
        return result

    def get_mcp_config_paths(self) -> List[Path]:
        """Get MCP configuration paths for Claude Code."""
        return []

    def get_workspace_mcp_config_paths(self, workspace: Union[Path, str]) -> List[Path]:
        """Get workspace-specific MCP configuration files (.mcp.json)."""
        if isinstance(workspace, str):
            workspace = Path(workspace)

        mcp_json_path = workspace / ".mcp.json"
        return [mcp_json_path] if mcp_json_path.exists() else []

    def get_global_rules(self) -> List[Rule]:
        """
        Get global rules/memory for Claude Code.

        Global memory is defined in:
        - ~/.claude/CLAUDE.md (User memory - personal preferences for all projects)
        """
        if self.global_memory_path.exists():
            return [Rule(pattern=self.global_memory_path)]
        return []

    def get_prompts(self, workspace: Union[Path, str, None] = None) -> List[Rule]:
        """
        Get custom slash commands for Claude Code.

        Custom commands are defined in:
        - ~/.claude/commands/*.md (global commands available in all projects)
        - .claude/commands/*.md (project-specific commands)
        """
        rules = []

        # Global commands
        global_commands_dir = Path.home() / ".claude" / "commands"
        if global_commands_dir.exists():
            rules.extend(Rule(pattern=f) for f in global_commands_dir.glob("*.md"))

        # Project-specific commands
        if workspace:
            if isinstance(workspace, str):
                workspace = Path(workspace)

            project_commands_dir = workspace / ".claude" / "commands"
            if project_commands_dir.exists():
                rules.extend(Rule(pattern=f) for f in project_commands_dir.glob("*.md"))

        return rules

    def get_workspace_rules(self, workspace: Union[Path, str]) -> List[Rule]:
        """
        Get workspace-level rules for Claude Code.

        Workspace rules/memory can be defined in:
        - CLAUDE.md and CLAUDE.local.md files in the workspace directory and parent directories
        - CLAUDE.md and CLAUDE.local.md files in child directories (searched recursively)
        """
        rules = []

        if isinstance(workspace, str):
            workspace = Path(workspace)

        # Search parent directories
        current_dir = workspace.resolve().parent
        while current_dir != current_dir.parent:
            for filename in ["CLAUDE.md", "CLAUDE.local.md"]:
                file_path = current_dir / filename
                if file_path.exists():
                    rules.append(Rule(pattern=file_path))
            current_dir = current_dir.parent

        # Search current directory and all subdirectories
        for pattern in ["**/CLAUDE.md", "**/CLAUDE.local.md"]:
            rules.extend(Rule(pattern=p) for p in workspace.glob(pattern))

        return rules