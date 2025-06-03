import json
import os
from pathlib import Path
from typing import List, Union

from rich.console import Console

from agapps.schema import AgentApp, MCP, MCPConfig, Rule, RuleConfig, PromptConfig

console = Console()


class Zed(AgentApp):
    supports_global_mcps = True
    supports_global_rules = False  # Rules Library is not accessible via filesystem
    supports_workspace_rules = True
    supports_global_prompts = False  # Rules Library is internal
    supports_workspace_prompts = False

    def __init__(self):
        super().__init__(name="Zed")

        # Configuration directory path (same for all platforms)
        # According to docs: ~/.config/zed/settings.json by default
        # or $XDG_CONFIG_HOME/zed/settings.json if XDG_CONFIG_HOME is set
        if "XDG_CONFIG_HOME" in os.environ:
            self.config_dir = Path(os.environ["XDG_CONFIG_HOME"]) / "zed"
        else:
            self.config_dir = Path.home() / ".config" / "zed"

        self.settings_path = self.config_dir / "settings.json"

    def get_mcps(
        self, workspace: Union[Path, str, None] = None
    ) -> Union[List[MCPConfig], None]:
        """
        Get MCP configurations from Zed.

        Zed's MCPs (called "context servers") are defined in settings.json
        under the "context_servers" key.
        """
        configs = []

        if self.settings_path.exists():
            try:
                with open(self.settings_path, "r") as f:
                    # Zed uses JSON with comments, but we'll try to parse as regular JSON
                    content = f.read()
                    # Remove comments for JSON parsing (basic implementation)
                    lines = content.split("\n")
                    filtered_lines = []
                    for line in lines:
                        # Remove // comments (basic implementation)
                        if "//" in line:
                            comment_pos = line.find("//")
                            # Check if // is not inside a string
                            quote_count = line[:comment_pos].count('"') - line[
                                :comment_pos
                            ].count('\\"')
                            if (
                                quote_count % 2 == 0
                            ):  # Even number of quotes means // is outside strings
                                line = line[:comment_pos].rstrip()
                        filtered_lines.append(line)

                    cleaned_content = "\n".join(filtered_lines)
                    config = json.loads(cleaned_content)

                if not isinstance(config, dict):
                    console.print(
                        f"[yellow]Warning: Zed settings file {self.settings_path} should contain a JSON object, got {type(config).__name__}[/yellow]"
                    )
                    return configs

                servers = []
                context_servers = config.get("context_servers", {})

                if not isinstance(context_servers, dict):
                    console.print(
                        f"[yellow]Warning: context_servers in {self.settings_path} should be an object, got {type(context_servers).__name__}[/yellow]"
                    )
                    return configs

                for server_name, server_details in context_servers.items():
                    if not isinstance(server_details, dict):
                        continue

                    # Handle command-based MCP servers (direct command-line)
                    command_config = server_details.get("command", {})
                    if isinstance(command_config, dict) and command_config.get("path"):
                        command_path = command_config.get("path", "")
                        args = command_config.get("args", [])
                        env_vars = command_config.get("env", {})

                        full_command = command_path
                        if isinstance(args, list) and args:
                            full_command = f"{command_path} {' '.join(args)}".strip()
                        elif isinstance(args, str) and args:
                            full_command = f"{command_path} {args}".strip()

                        servers.append(
                            MCP(
                                name=server_name,
                                command=full_command,
                                envs=env_vars or {},
                            )
                        )

                    # Handle extension-based MCP servers (only settings, no command)
                    elif (
                        "settings" in server_details and "command" not in server_details
                    ):
                        # Extension-based MCP server - command is handled by extension
                        servers.append(
                            MCP(
                                name=server_name,
                                command=f"<zed-extension:{server_name}>",  # Indicate it's an extension
                                envs={},  # Extensions don't use env vars in the same way
                            )
                        )

                if servers:
                    configs.append(
                        MCPConfig(
                            path=self.settings_path, type="global", servers=servers
                        )
                    )

            except json.JSONDecodeError as e:
                console.print(
                    f"[yellow]Warning: Invalid JSON in Zed settings file {self.settings_path}: {e}[/yellow]"
                )
            except IOError as e:
                console.print(
                    f"[yellow]Warning: Could not read Zed settings file {self.settings_path}: {e}[/yellow]"
                )

        return configs

    def get_rules(
        self, workspace: Union[Path, str, None] = None
    ) -> Union[List[RuleConfig], None]:
        """
        Get rule configurations for Zed.

        Rules include:
        - Workspace: .rules files and other supported rule files in the project root

        Note: Zed's Rules Library is stored internally and not accessible via filesystem paths.
        """
        configs = []

        # Workspace rules
        if workspace:
            if isinstance(workspace, str):
                workspace = Path(workspace)

            workspace_rules = []

            # Look for supported rule files as documented in Zed docs
            # The first file which matches in this list will be used
            rule_file_names = [
                ".rules",
                ".cursorrules",
                ".windsurfrules",
                ".clinerules",
                ".github/copilot-instructions.md",
                "CLAUDE.md",
            ]

            for rule_file_name in rule_file_names:
                if "/" in rule_file_name:
                    # Handle nested paths like .github/copilot-instructions.md
                    rule_file = workspace / rule_file_name
                else:
                    rule_file = workspace / rule_file_name

                if rule_file.exists() and rule_file.is_file():
                    workspace_rules.append(Rule(pattern=rule_file))
                    break  # Use the first matching rule file

            if workspace_rules:
                configs.append(
                    RuleConfig(
                        path=workspace,
                        type="workspace",
                        rules=workspace_rules,
                    )
                )

        return configs

    def get_prompts(
        self, workspace: Union[Path, str, None] = None
    ) -> Union[List[PromptConfig], None]:
        """
        Get prompt configurations for Zed.

        Zed's Rules Library stores prompts/rules internally and is not accessible
        via filesystem paths. According to the documentation, rules are "stored locally"
        but the exact storage mechanism is not exposed to the filesystem.
        """
        # Zed's Rules Library is internal - not accessible via file system
        return None
