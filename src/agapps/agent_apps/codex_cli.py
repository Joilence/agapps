import os
import json
import yaml
from pathlib import Path
from typing import List, Union, Dict

from agapps.schema import AgentApp, MCP, MCPConfig, Rule, RuleConfig, Prompt, PromptConfig


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
                except (json.JSONDecodeError, yaml.YAMLError, IOError):
                    pass
        return {}

    def get_mcps(self, workspace: Union[Path, str, None] = None) -> Union[List[MCPConfig], None]:
        """
        Get MCP configurations from Codex CLI.

        Note: Codex CLI doesn't have built-in MCP support.
        """
        return None

    def get_rules(self, workspace: Union[Path, str, None] = None) -> Union[List[RuleConfig], None]:
        """
        Get rule configurations for Codex CLI.

        Rules include:
        - Global: ~/.codex/AGENTS.md
        """
        configs = []
        
        # Global rules
        if self.instructions_path.exists():
            configs.append(RuleConfig(
                path=self.instructions_path,
                type="global",
                rules=[Rule(pattern=self.instructions_path)]
            ))
        
        # Codex CLI doesn't support workspace-specific rules
        
        return configs

    def get_prompts(self, workspace: Union[Path, str, None] = None) -> Union[List[PromptConfig], None]:
        """
        Get prompt configurations for Codex CLI.
        
        Codex CLI doesn't have a built-in prompt/command system.
        """
        return None