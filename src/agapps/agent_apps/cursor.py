import json
from pathlib import Path
from typing import List, Union

from agapps.schema import AgentApp, MCP, MCPConfig, Rule, RuleConfig, PromptConfig


class Cursor(AgentApp):
    def __init__(self):
        super().__init__(name="Cursor")
        self.global_rules_path = Path.home() / ".cursor" / "global_rules.md"
        self.mcp_config_path = Path.home() / ".cursor" / "mcp.json"

    def get_mcps(
        self, workspace: Union[Path, str, None] = None
    ) -> Union[List[MCPConfig], None]:
        """
        Get MCP configurations from Cursor.

        Cursor's MCPs are defined in ~/.cursor/mcp.json with "mcpServers" object
        where each key is the server name and value contains command, args, env.
        """
        configs = []

        if self.mcp_config_path.exists():
            try:
                with open(self.mcp_config_path, "r") as f:
                    config = json.load(f)

                servers = []
                mcp_servers = config.get("mcpServers", {})

                for server_name, server_details in mcp_servers.items():
                    if not isinstance(server_details, dict):
                        continue

                    command = server_details.get("command", "")
                    args = server_details.get("args", [])
                    env_vars = server_details.get("env", {})

                    # Build full command
                    if args:
                        if isinstance(args, list):
                            full_command = f"{command} {' '.join(args)}".strip()
                        else:
                            full_command = f"{command} {args}".strip()
                    else:
                        full_command = command

                    if command:
                        servers.append(
                            MCP(name=server_name, command=full_command, envs=env_vars)
                        )

                if servers:
                    configs.append(
                        MCPConfig(
                            path=self.mcp_config_path, type="global", servers=servers
                        )
                    )

            except (json.JSONDecodeError, IOError):
                pass

        return configs

    def get_rules(
        self, workspace: Union[Path, str, None] = None
    ) -> Union[List[RuleConfig], None]:
        """
        Get rule configurations for Cursor.

        Rules include:
        - Global: ~/.cursor/global_rules.md
        - Workspace: .cursorrules and .cursorrules.local files
        """
        configs = []

        # Global rules
        if self.global_rules_path.exists():
            configs.append(
                RuleConfig(
                    path=self.global_rules_path,
                    type="global",
                    rules=[Rule(pattern=self.global_rules_path)],
                )
            )

        # Workspace rules
        if workspace:
            if isinstance(workspace, str):
                workspace = Path(workspace)

            workspace_rules = []

            # Check for .cursorrules
            cursorrules_path = workspace / ".cursorrules"
            if cursorrules_path.exists():
                workspace_rules.append(Rule(pattern=cursorrules_path))

            # Check for .cursorrules.local
            cursorrules_local_path = workspace / ".cursorrules.local"
            if cursorrules_local_path.exists():
                workspace_rules.append(Rule(pattern=cursorrules_local_path))

            if workspace_rules:
                configs.append(
                    RuleConfig(path=workspace, type="workspace", rules=workspace_rules)
                )

        return configs

    def get_prompts(
        self, workspace: Union[Path, str, None] = None
    ) -> Union[List[PromptConfig], None]:
        """
        Get prompt configurations for Cursor.

        Cursor doesn't have a built-in prompt/command system like Claude Code.
        """
        return None
