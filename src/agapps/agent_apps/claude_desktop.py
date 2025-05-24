import os
import json
from pathlib import Path
from typing import List, Union, Dict

from agapps.schema import AgentApp, MCP, MCPConfig, Rule, RuleConfig, Prompt, PromptConfig


class ClaudeDesktop(AgentApp):
    def __init__(self):
        super().__init__(name="Claude Desktop")
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

    def get_mcps(self, workspace: Union[Path, str, None] = None) -> Union[List[MCPConfig], None]:
        """
        Get MCP configurations from Claude desktop config.

        The config file has a "mcpServers" key with an array of server specifications.
        Each spec includes name, command, args, env, cwd, etc.
        """
        configs = []
        config_path = self.get_config_path()
        
        if config_path.exists():
            config = self.read_config()
            mcp_servers = config.get("mcpServers", {})
            servers = []

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
                configs.append(MCPConfig(path=config_path, type="global", servers=servers))
        
        return configs

    def get_rules(self, workspace: Union[Path, str, None] = None) -> Union[List[RuleConfig], None]:
        """
        Get rule configurations for Claude Desktop.
        
        Claude Desktop doesn't have built-in rule files like other agent apps.
        """
        return None

    def get_prompts(self, workspace: Union[Path, str, None] = None) -> Union[List[PromptConfig], None]:
        """
        Get prompt configurations for Claude Desktop.
        
        Claude Desktop doesn't have custom prompt/command files.
        """
        return None