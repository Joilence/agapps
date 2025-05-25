import json
from pathlib import Path
from typing import List, Union

from agapps.schema import AgentApp, MCP, MCPConfig, Rule, RuleConfig, PromptConfig


class Windsurf(AgentApp):
    def __init__(self):
        super().__init__(name="Windsurf")
        self.codeium_memories_path = Path.home() / ".codeium" / "windsurf" / "memories"
        self.mcp_config_paths = [
            Path.home() / ".codeium" / "windsurf" / "mcp_config.json",
        ]

    def get_mcps(
        self, workspace: Union[Path, str, None] = None
    ) -> Union[List[MCPConfig], None]:
        """
        Get MCP configurations from Windsurf.

        Windsurf's MCPs are defined in ~/.codeium/windsurf/mcp_config.json
        """
        configs = []

        for config_path in self.mcp_config_paths:
            if config_path.exists():
                try:
                    with open(config_path, "r") as f:
                        config = json.load(f)

                    servers = []
                    mcp_servers = config.get("mcpServers", {})

                    for server_name, server_details in mcp_servers.items():
                        if not isinstance(server_details, dict):
                            continue

                        command_executable = server_details.get("command", "")
                        args = server_details.get("args", [])
                        env_vars = server_details.get("env", {})

                        full_command = command_executable
                        if isinstance(args, list) and args:
                            full_command = (
                                f"{command_executable} {' '.join(args)}".strip()
                            )
                        elif isinstance(args, str) and args:
                            full_command = f"{command_executable} {args}".strip()

                        if command_executable:
                            servers.append(
                                MCP(
                                    name=server_name,
                                    command=full_command,
                                    envs=env_vars,
                                )
                            )

                    if servers:
                        configs.append(
                            MCPConfig(path=config_path, type="global", servers=servers)
                        )

                except (json.JSONDecodeError, IOError):
                    pass

        return configs

    def get_rules(
        self, workspace: Union[Path, str, None] = None
    ) -> Union[List[RuleConfig], None]:
        """
        Get rule configurations for Windsurf.

        Rules include:
        - Global: ~/.codeium/windsurf/memories
        - Workspace: .windsurf/memories
        """
        configs = []

        # Global rules
        if self.codeium_memories_path.exists():
            configs.append(
                RuleConfig(
                    path=self.codeium_memories_path,
                    type="global",
                    rules=[Rule(pattern=self.codeium_memories_path)],
                )
            )

        # Workspace rules
        if workspace:
            if isinstance(workspace, str):
                workspace = Path(workspace)

            memories_path = workspace / ".windsurf" / "memories"
            if memories_path.exists():
                configs.append(
                    RuleConfig(
                        path=memories_path,
                        type="workspace",
                        rules=[Rule(pattern=memories_path)],
                    )
                )

        return configs

    def get_prompts(
        self, workspace: Union[Path, str, None] = None
    ) -> Union[List[PromptConfig], None]:
        """
        Get prompt configurations for Windsurf.

        Windsurf doesn't have a built-in prompt/command system.
        """
        return None
