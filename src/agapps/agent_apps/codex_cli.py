import yaml
import json
from pathlib import Path
from typing import List, Union, Dict

from agapps.schema import AgentApp, MCP, Rule


class CodexCli(AgentApp):
    def __init__(self):
        super().__init__(name="OpenAI Codex CLI")
        self.config_paths = [
            Path.home() / ".codex" / "config.yaml",
            Path.home() / ".codex" / "config.json",
        ]
        self.instructions_path = Path.home() / ".codex" / "AGENTS.md"

    def read_config(self) -> Dict:
        """Read the Codex CLI config file if it exists."""
        for config_path in self.config_paths:
            if config_path.exists():
                try:
                    with open(config_path, "r") as f:
                        if config_path.suffix == ".yaml":
                            return yaml.safe_load(f) or {}
                        else:
                            return json.load(f)
                except (yaml.YAMLError, json.JSONDecodeError, IOError):
                    pass
        return {}

    def get_mcps(self, workspace: Union[Path, str, None] = None) -> List[MCP]:
        """
        Get MCP configurations from Codex CLI.

        Codex CLI is an MCP client only; it does not load external servers.
        """
        return []

    def get_mcp_config_paths(self) -> List[Path]:
        """Codex CLI does not load external MCP servers from config files."""
        return []

    def get_global_rules(self) -> List[Rule]:
        """
        Get global rules for Codex CLI.

        Global rules are defined in ~/.codex/AGENTS.md file.
        """
        rules = []

        if self.instructions_path.exists():
            rules.append(Rule(pattern=self.instructions_path))

        return rules

    def get_workspace_rules(self, workspace: Union[Path, str]) -> List[Rule]:
        """
        Get workspace-level rules for Codex CLI.

        Workspace rules are defined in AGENTS.md in the project root
        or current working directory.
        """
        rules = []

        # Convert workspace to Path if it's a string
        if isinstance(workspace, str):
            workspace = Path(workspace)

        # Check for AGENTS.md in project root / current workspace context
        agents_md = workspace / "AGENTS.md"
        if agents_md.exists():
            rules.append(Rule(pattern=agents_md))

        return rules 