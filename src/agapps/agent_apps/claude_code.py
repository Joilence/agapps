import os
import json
from pathlib import Path
from typing import List, Union, Dict

from agapps.schema import AgentApp, MCP, MCPConfig, Rule, RuleConfig, Prompt, PromptConfig


class ClaudeCode(AgentApp):
    def __init__(self):
        super().__init__(name="Claude Code")
        self.global_memory_path = Path.home() / ".claude" / "CLAUDE.md"

    def get_mcps(self, workspace: Union[Path, str, None] = None) -> Union[List[MCPConfig], None]:
        """
        Get MCP configurations for Claude Code from .mcp.json files.
        """
        configs = []
        
        if workspace:
            if isinstance(workspace, str):
                workspace = Path(workspace)
                
            mcp_json_path = workspace / ".mcp.json"
            if mcp_json_path.exists():
                try:
                    with open(mcp_json_path, "r") as f:
                        data = json.load(f)
                    
                    servers = []
                    mcp_servers = data.get("mcpServers", {})
                    
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
                            servers.append(MCP(name=server_name, command=full_command, envs=env_vars))
                    
                    if servers:
                        configs.append(MCPConfig(path=mcp_json_path, type="workspace", servers=servers))
                        
                except (json.JSONDecodeError, IOError):
                    pass
                    
        return configs

    def get_rules(self, workspace: Union[Path, str, None] = None) -> Union[List[RuleConfig], None]:
        """
        Get rule configurations for Claude Code.
        
        Rules include:
        - Global: ~/.claude/CLAUDE.md
        - Workspace: CLAUDE.md and CLAUDE.local.md files in workspace and parents/children
        """
        configs = []
        
        # Global rules
        if self.global_memory_path.exists():
            configs.append(RuleConfig(
                path=self.global_memory_path,
                type="global",
                rules=[Rule(pattern=self.global_memory_path)]
            ))
        
        # Workspace rules
        if workspace:
            if isinstance(workspace, str):
                workspace = Path(workspace)
            
            workspace_rules = []
            
            # Search parent directories
            current_dir = workspace.resolve().parent
            while current_dir != current_dir.parent:
                for filename in ["CLAUDE.md", "CLAUDE.local.md"]:
                    file_path = current_dir / filename
                    if file_path.exists():
                        workspace_rules.append(Rule(pattern=file_path))
                current_dir = current_dir.parent
            
            # Search current directory and all subdirectories
            for pattern in ["**/CLAUDE.md", "**/CLAUDE.local.md"]:
                workspace_rules.extend(Rule(pattern=p) for p in workspace.glob(pattern))
            
            if workspace_rules:
                configs.append(RuleConfig(
                    path=workspace,
                    type="workspace",
                    rules=workspace_rules
                ))
        
        return configs

    def get_prompts(self, workspace: Union[Path, str, None] = None) -> Union[List[PromptConfig], None]:
        """
        Get custom slash commands for Claude Code.

        Custom commands are defined in:
        - ~/.claude/commands/*.md (global commands available in all projects)
        - .claude/commands/*.md (project-specific commands)
        """
        configs = []
        
        # Global commands
        global_commands_dir = Path.home() / ".claude" / "commands"
        if global_commands_dir.exists():
            prompts = [Prompt(pattern=f) for f in global_commands_dir.glob("*.md")]
            if prompts:
                configs.append(PromptConfig(
                    path=global_commands_dir,
                    type="global",
                    prompts=prompts
                ))
        
        # Workspace commands
        if workspace:
            if isinstance(workspace, str):
                workspace = Path(workspace)
            
            project_commands_dir = workspace / ".claude" / "commands"
            if project_commands_dir.exists():
                prompts = [Prompt(pattern=f) for f in project_commands_dir.glob("*.md")]
                if prompts:
                    configs.append(PromptConfig(
                        path=project_commands_dir,
                        type="workspace",
                        prompts=prompts
                    ))
        
        return configs