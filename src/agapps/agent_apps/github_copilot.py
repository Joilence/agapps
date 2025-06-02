import os
import json
from pathlib import Path
from typing import List, Union, Dict

from agapps.schema import AgentApp, MCP, MCPConfig, Rule, RuleConfig, PromptConfig


class GitHubCopilot(AgentApp):
    supports_global_mcps = True
    supports_workspace_rules = True

    def __init__(self):
        super().__init__(name="GitHub Copilot")
        self.vscode_settings_paths = {
            "darwin": Path.home()
            / "Library"
            / "Application Support"
            / "Code"
            / "User"
            / "settings.json",
            "windows": Path(os.environ.get("APPDATA", ""))
            / "Code"
            / "User"
            / "settings.json",
            "linux": Path.home() / ".config" / "Code" / "User" / "settings.json",
        }
        self.jetbrains_mcp_paths = {
            "darwin": Path.home()
            / ".config"
            / "github-copilot"
            / "intellij"
            / "mcp.json",
            "windows": Path.home()
            / ".config"
            / "github-copilot"
            / "intellij"
            / "mcp.json",
            "linux": Path.home()
            / ".config"
            / "github-copilot"
            / "intellij"
            / "mcp.json",
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
            # Default to Linux path
            return self.vscode_settings_paths["linux"]

    def get_jetbrains_mcp_path(self) -> Path:
        """Get the platform-specific path to JetBrains IDE MCP configuration."""
        platform = os.uname().sysname.lower()
        if "darwin" in platform:
            return self.jetbrains_mcp_paths["darwin"]
        elif "windows" in platform:
            return self.jetbrains_mcp_paths["windows"]
        elif "linux" in platform:
            return self.jetbrains_mcp_paths["linux"]
        else:
            # Default to Linux path
            return self.jetbrains_mcp_paths["linux"]

    def read_vscode_settings(self) -> Dict:
        """Read VS Code settings file."""
        settings_path = self.get_vscode_settings_path()
        if not settings_path.exists():
            return {}

        try:
            with open(settings_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def get_mcps(
        self, workspace: Union[Path, str, None] = None
    ) -> Union[List[MCPConfig], None]:
        """
        Get MCP configurations for GitHub Copilot.

        GitHub Copilot Chat supports MCP servers when enabled in VS Code settings
        and also in JetBrains IDEs.
        """
        configs = []

        # Check VS Code settings
        settings = self.read_vscode_settings()

        # Check if MCP discovery is enabled in VS Code
        if settings.get("chat.mcp.discovery.enabled", False):
            # Check for configured MCP servers in VS Code
            mcp_servers = settings.get("chat.mcp.servers", {})
            servers = []

            for server_name, server_details in mcp_servers.items():
                if not isinstance(server_details, dict):
                    continue

                command = server_details.get("command", "")
                args = server_details.get("args", [])
                env_vars = server_details.get("env", {})

                full_command = command
                if isinstance(args, list) and args:
                    full_command = f"{command} {' '.join(args)}".strip()
                elif isinstance(args, str) and args:
                    full_command = f"{command} {args}".strip()

                if command:
                    servers.append(
                        MCP(name=server_name, command=full_command, envs=env_vars)
                    )

            if servers:
                configs.append(
                    MCPConfig(
                        path=self.get_vscode_settings_path(),
                        type="global",
                        servers=servers,
                    )
                )

        # Check JetBrains IDE MCP configuration
        jetbrains_mcp_path = self.get_jetbrains_mcp_path()
        if jetbrains_mcp_path.exists():
            try:
                with open(jetbrains_mcp_path, "r") as f:
                    jetbrains_config = json.load(f)

                jetbrains_servers = []
                mcp_servers = jetbrains_config.get("servers", {})

                for server_name, server_details in mcp_servers.items():
                    if not isinstance(server_details, dict):
                        continue

                    # JetBrains format has "type": "stdio" field
                    if server_details.get("type") != "stdio":
                        continue

                    command = server_details.get("command", "")
                    args = server_details.get("args", [])
                    env_vars = server_details.get("env", {})

                    full_command = command
                    if isinstance(args, list) and args:
                        full_command = f"{command} {' '.join(args)}".strip()
                    elif isinstance(args, str) and args:
                        full_command = f"{command} {args}".strip()

                    if command:
                        jetbrains_servers.append(
                            MCP(name=server_name, command=full_command, envs=env_vars)
                        )

                if jetbrains_servers:
                    configs.append(
                        MCPConfig(
                            path=jetbrains_mcp_path,
                            type="global",
                            servers=jetbrains_servers,
                        )
                    )
            except (json.JSONDecodeError, IOError):
                pass

        return configs

    def get_rules(
        self, workspace: Union[Path, str, None] = None
    ) -> Union[List[RuleConfig], None]:
        """
        Get rule configurations for GitHub Copilot.

        Rules include:
        - Global: VS Code settings (github.copilot.instructions)
        - Workspace: .github/copilot-instructions.md
        """
        configs = []

        # Global rules from VS Code settings
        settings = self.read_vscode_settings()
        instructions = settings.get("github.copilot.instructions", None)

        if instructions:
            # Create a virtual rule for the instructions in settings
            configs.append(
                RuleConfig(
                    path=self.get_vscode_settings_path(),
                    type="global",
                    rules=[Rule(pattern=self.get_vscode_settings_path())],
                )
            )

        # Workspace rules
        if workspace:
            if isinstance(workspace, str):
                workspace = Path(workspace)

            instructions_path = workspace / ".github" / "copilot-instructions.md"
            if instructions_path.exists():
                configs.append(
                    RuleConfig(
                        path=instructions_path.parent,
                        type="workspace",
                        rules=[Rule(pattern=instructions_path)],
                    )
                )

        return configs

    def get_prompts(
        self, workspace: Union[Path, str, None] = None
    ) -> Union[List[PromptConfig], None]:
        """
        Get prompt configurations for GitHub Copilot.

        GitHub Copilot doesn't have a built-in prompt/command system like Claude Code.
        """
        return None
