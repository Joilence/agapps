import json
from pathlib import Path
from typing import List, Tuple, Union

from agapps.schema import AgentApp, MCP, Rule # Updated import


class Cursor(AgentApp):
    def __init__(self):
        super().__init__(name="Cursor")
        self.global_rules_path = Path.home() / ".cursor" / "global_rules.md"
        self.mcp_config_path = Path.home() / ".cursor" / "mcp.json"

    def get_mcps(self) -> List[MCP]:
        """
        Get MCP configurations from Cursor.

        Cursor's MCPs are defined in ~/.cursor/mcp.json with "mcpServers" object
        where each key is the server name and value contains command, args, env.
        """
        result = []

        if not self.mcp_config_path.exists():
            return result

        try:
            with open(self.mcp_config_path, "r") as f:
                config = json.load(f)

            # Extract MCP servers from config
            if "mcpServers" in config and isinstance(config["mcpServers"], dict):
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

                        result.append(MCP(name=server_name, command=command, envs=envs))
        except (json.JSONDecodeError, IOError):
            # Failed to parse config
            pass

        return result

    def get_mcp_config_paths(self) -> List[Path]:
        """Get the path to the Cursor MCP config file if it exists and contains MCPs."""
        if self.mcp_config_path.exists():
            try:
                with open(self.mcp_config_path, "r") as f:
                    config = json.load(f)
                if config.get("mcpServers"):
                    return [self.mcp_config_path]
            except (json.JSONDecodeError, IOError):
                pass
        return []

    def get_global_rules(self) -> List[Rule]:
        """
        Get global rules for Cursor.

        Global rules are stored in ~/.cursor/global_rules.md.
        """
        rules = []

        if self.global_rules_path.exists():
            rules.append(Rule(pattern=self.global_rules_path))

        return rules

    def get_workspace_rules(self, workspace: Union[Path, str]) -> List[Rule]:
        """
        Get workspace-level rules for Cursor.

        Workspace rules can be defined in:
        - .cursorrules (single file - legacy)
        - .cursor/rules/*.md (multi-file rules)
        """
        rules = []

        # Convert workspace to Path if it's a string
        if isinstance(workspace, str):
            workspace = Path(workspace)

        # Check for legacy .cursorrules file
        legacy_rules = workspace / ".cursorrules"
        if legacy_rules.exists():
            rules.append(Rule(pattern=legacy_rules))

        # Check for .cursor/rules directory with .md files
        rules_dir = workspace / ".cursor" / "rules"
        if rules_dir.exists() and rules_dir.is_dir():
            # Add all .md and .mdc files in the rules directory
            for rule_file in rules_dir.glob("*.md*"):
                if rule_file.exists():
                    rules.append(Rule(pattern=rule_file))

        return rules 