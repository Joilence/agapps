import json
from pathlib import Path
from typing import List, Tuple, Union

from agapps.schema import AgentApp, MCP, Rule # Updated import


class Windsurf(AgentApp):
    def __init__(self):
        super().__init__(name="Windsurf")
        self.codeium_memories_path = Path.home() / ".codeium" / "windsurf" / "memories"
        self.mcp_config_paths = [
            Path.home() / ".codeium" / "windsurf" / "mcp_config.json",
        ]

    def get_mcps(self, workspace: Union[Path, str, None] = None) -> List[MCP]:
        """
        Get MCP configurations from Windsurf.

        Windsurf MCPs are defined in ~/.codeium/windsurf/mcp_config.json
        with a "mcpServers" object where each key is the server name and value contains command, args, env.
        """
        result = []

        # Check all possible MCP config locations
        for config_path in self.mcp_config_paths:
            if config_path.exists():
                try:
                    with open(config_path, "r") as f:
                        config = json.load(f)

                    # Extract MCP servers from config
                    if "mcpServers" in config and isinstance(
                        config["mcpServers"], dict
                    ):
                        for server_name, server_config in config["mcpServers"].items():
                            if isinstance(server_config, dict):
                                command = server_config.get("command", "")
                                args = server_config.get("args", [])

                                # For SSE servers, there's usually a URL instead
                                if not command and "url" in server_config:
                                    command = f"SSE Server: {server_config['url']}"
                                elif args:
                                    # Combine command and args for display
                                    command = f"{command} {' '.join(args)}"

                                # Extract environment variables if available
                                envs = server_config.get("env", {})

                                result.append(
                                    MCP(name=server_name, command=command, envs=envs)
                                )
                except (json.JSONDecodeError, IOError):
                    # Failed to parse config
                    pass

        return result

    def get_mcp_config_paths(self) -> List[Path]:
        """Get the paths to Windsurf MCP config files that exist and contain MCPs."""
        found_paths = []
        for config_path in self.mcp_config_paths:
            if config_path.exists():
                try:
                    with open(config_path, "r") as f:
                        config = json.load(f)
                    if config.get("mcpServers"):
                        found_paths.append(config_path)
                except (json.JSONDecodeError, IOError):
                    pass # Ignore if a file is invalid
        return found_paths

    def get_global_rules(self) -> List[Rule]:
        """
        Get global rules for Windsurf.

        Global rules are defined in ~/.codeium/windsurf/memories/*.md
        """
        rules = []
            
        # Check for memories in .codeium/windsurf/memories/*.md
        if self.codeium_memories_path.exists() and self.codeium_memories_path.is_dir():
            for memory_file in self.codeium_memories_path.glob("*.md"):
                if memory_file.exists():
                    rules.append(Rule(pattern=memory_file))

        return rules

    def get_workspace_rules(self, workspace: Union[Path, str]) -> List[Rule]:
        """
        Get workspace-level rules for Windsurf.

        Workspace-level rules can be defined in:
        - .windsurfrules (single file format - v4 syntax)
        - .windsurf/rules/*.md (multi-file rules - v5 syntax)
        """
        rules = []

        # Convert workspace to Path if it's a string
        if isinstance(workspace, str):
            workspace = Path(workspace)

        # Check for single file rules
        single_file_rules = workspace / ".windsurfrules"
        if single_file_rules.exists():
            rules.append(Rule(pattern=single_file_rules))

        # Check for multi-file rules
        rules_dir = workspace / ".windsurf" / "rules"
        if rules_dir.exists() and rules_dir.is_dir():
            # Add all .md files in the rules directory
            for rule_file in rules_dir.glob("*.md"):
                if rule_file.exists():
                    rules.append(Rule(pattern=rule_file))

        return rules 