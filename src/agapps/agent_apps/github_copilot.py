from pathlib import Path
from typing import List, Union

from agapps.schema import AgentApp, MCP, Rule


class GitHubCopilot(AgentApp):
    def __init__(self):
        super().__init__(name="GitHub Copilot")

    def get_mcps(self) -> List[MCP]:
        """
        Get MCP configurations for GitHub Copilot.
        
        GitHub Copilot does not support MCP configurations.
        """
        return []

    def get_mcp_config_paths(self) -> List[Path]:
        """Get MCP config file paths for GitHub Copilot."""
        return []

    def get_global_rules(self) -> List[Rule]:
        """
        Get global rules for GitHub Copilot.
        
        GitHub Copilot does not support global rules/instructions.
        All customization is done at the repository level.
        """
        return []

    def get_workspace_rules(self, workspace: Union[Path, str]) -> List[Rule]:
        """
        Get workspace-level rules for GitHub Copilot.

        GitHub Copilot supports repository custom instructions and prompt files:
        - .github/copilot-instructions.md (Repository custom instructions)
        - .github/prompts/*.prompt.md (Prompt files for VS Code)
        """
        rules = []

        # Convert workspace to Path if it's a string
        if isinstance(workspace, str):
            workspace = Path(workspace)

        # Check for repository custom instructions
        copilot_instructions_path = workspace / ".github" / "copilot-instructions.md"
        if copilot_instructions_path.exists():
            rules.append(Rule(pattern=copilot_instructions_path))

        # Check for prompt files in .github/prompts/ directory
        prompts_dir = workspace / ".github" / "prompts"
        if prompts_dir.exists() and prompts_dir.is_dir():
            # Add all .prompt.md files in the prompts directory
            for prompt_file in prompts_dir.glob("*.prompt.md"):
                rules.append(Rule(pattern=prompt_file))

        return rules