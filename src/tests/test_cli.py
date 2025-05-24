import pytest
from click.testing import CliRunner
from pathlib import Path
from typing import List, Dict, Union, Type
import sys # Add sys import
import os # Add os import

from agapps.schema import AgentApp, MCP, Rule
from agapps.cli import cli, APPS as CLI_APPS # Import the CLI and its APPS dict

# --- Mock AgentApp Implementations ---

class MockAppAllFeatures(AgentApp):
    def __init__(self):
        super().__init__(name="AllFeatures App")

    def get_mcps(self, workspace: Union[Path, str, None] = None) -> List[MCP]:
        return [MCP(name="test_mcp", command="do_something", envs={"KEY": "VALUE"})]

    def get_mcp_config_paths(self) -> List[Path]:
        return [Path("~/.config/allfeatures/mcp.json")]

    def get_global_rules(self) -> List[Rule]:
        return [Rule(pattern=Path("~/.config/allfeatures/global.md"))]

    def get_workspace_rules(self, workspace: Union[Path, str]) -> List[Rule]:
        ws_path = Path(workspace)
        rule_file = ws_path / "allfeatures.rules.md"
        # To test print_rule_info reading file content, ensure the file is created in the test.
        return [Rule(pattern=rule_file)]

class MockAppNoMCPs(AgentApp):
    def __init__(self):
        super().__init__(name="NoMCPs App")

    def get_mcps(self, workspace: Union[Path, str, None] = None) -> List[MCP]:
        return []

    def get_mcp_config_paths(self) -> List[Path]:
        return []

    def get_global_rules(self) -> List[Rule]:
        return [Rule(pattern=Path("~/.config/nomcps/global.md"))]

    def get_workspace_rules(self, workspace: Union[Path, str]) -> List[Rule]:
        return [Rule(pattern=Path(workspace) / "nomcps.rules.md")]

class MockAppNoGlobalRules(AgentApp):
    def __init__(self):
        super().__init__(name="NoGlobalRules App")

    def get_mcps(self, workspace: Union[Path, str, None] = None) -> List[MCP]:
        return [MCP(name="another_mcp", command="do_else")]

    def get_mcp_config_paths(self) -> List[Path]:
        return [Path("~/.config/noglobal/mcp.json")]

    def get_global_rules(self) -> List[Rule]:
        return []

    def get_workspace_rules(self, workspace: Union[Path, str]) -> List[Rule]:
        return [Rule(pattern=Path(workspace) / "noglobal.rules.md")]

class MockAppNoWorkspaceRules(AgentApp):
    def __init__(self):
        super().__init__(name="NoWorkspaceRules App")
        # This app's get_workspace_rules returns [], so it effectively doesn't support them
        # which influences the 'list' command output.

    def get_mcps(self, workspace: Union[Path, str, None] = None) -> List[MCP]:
        return [MCP(name="ws_mcp", command="do_ws")]

    def get_mcp_config_paths(self) -> List[Path]:
        return [Path("~/.config/nows/mcp.json")]
    
    def get_global_rules(self) -> List[Rule]:
        return [Rule(pattern=Path("~/.config/nows/global.md"))]

    def get_workspace_rules(self, workspace: Union[Path, str]) -> List[Rule]:
        return [] # Explicitly no workspace rules

class MockAppNoFeatures(AgentApp):
    def __init__(self):
        super().__init__(name="NoFeatures App")

    def get_mcps(self, workspace: Union[Path, str, None] = None) -> List[MCP]:
        return []
    
    def get_mcp_config_paths(self) -> List[Path]:
        return []

    def get_global_rules(self) -> List[Rule]:
        return []

    def get_workspace_rules(self, workspace: Union[Path, str]) -> List[Rule]:
        return []

MOCK_APPS_CONFIG: Dict[str, Type[AgentApp]] = {
    "all-features": MockAppAllFeatures,
    "no-mcps": MockAppNoMCPs,
    "no-global": MockAppNoGlobalRules,
    "no-workspace": MockAppNoWorkspaceRules,
    "no-features": MockAppNoFeatures,
}

@pytest.fixture
def runner() -> CliRunner:
    # Attempt to ensure src is in path for tests
    # This should ideally be handled by pytest.ini_options pythonpath
    # but adding it here as a diagnostic step.
    project_root = Path(__file__).parent.parent.parent # Assuming tests are in src/tests/
    src_path = project_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    return CliRunner()

@pytest.fixture(autouse=True)
def mock_apps_dict(monkeypatch):
    # Ensure each test gets a fresh copy of the mock apps config
    # and that CLI_APPS is correctly patched.
    # Directly modifying CLI_APPS can cause issues if not careful with test isolation.
    # Instead, we'll patch it for the duration of each test.
    
    # Store original APPS
    original_apps = CLI_APPS.copy()
    
    # Patch with mocks
    CLI_APPS.clear()
    CLI_APPS.update(MOCK_APPS_CONFIG)
    
    yield # Test runs here

    # Restore original APPS
    CLI_APPS.clear()
    CLI_APPS.update(original_apps)


# --- Test Cases ---

def test_agapps_default_is_list(runner: CliRunner):
    """Test that `agapps` with no arguments defaults to `list` behavior."""
    result_default = runner.invoke(cli)
    result_list = runner.invoke(cli, ["list"])

    assert result_default.exit_code == 0
    assert "Installed Agent Apps" in result_default.output
    assert "AllFeatures App" in result_default.output
    assert "NoMCPs App" in result_default.output
    assert result_default.output == result_list.output

def test_agapps_list(runner: CliRunner):
    """Test `agapps list` command output."""
    result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0
    assert "Installed Agent Apps" in result.output
    # Check for app names
    assert "AllFeatures App" in result.output
    assert "NoMCPs App" in result.output
    assert "NoGlobalRules App" in result.output
    assert "NoWorkspaceRules App" in result.output
    assert "NoFeatures App" in result.output

    # Check for key elements for AllFeatures App
    assert "AllFeatures App" in result.output
    assert "Yes" in result.output # For MCPs, Global, Workspace - a bit simplistic but checks presence
    
    # Check for key elements for NoMCPs App
    # Expected: NoMCPs App | Yes | Yes | No 
    # The table output from rich might vary slightly in spacing.
    # We check for parts of the expected row.
    lines = result.output.splitlines()
    assert any("NoMCPs App" in line and "Yes" in line and "No" in line for line in lines)

    # Check for NoGlobalRules App: No | Yes | Yes
    assert any("NoGlobalRules App" in line and "No" in line and "Yes" in line for line in lines)
    
    # Check for NoWorkspaceRules App: Yes | No | Yes
    assert any("NoWorkspaceRules App" in line and "Yes" in line and "No" in line for line in lines)

    # Check for NoFeatures App: No | No | No
    assert any("NoFeatures App" in line and "No" in line and "No" in line and line.count("No") >= 3 for line in lines)


def test_agapps_view_workspace_path_valid(runner: CliRunner, tmp_path: Path):
    """Test `agapps view <WORKSPACE_PATH>` with a valid path."""
    rule_file_path = tmp_path / "allfeatures.rules.md"
    with open(rule_file_path, "w") as f:
        f.write("Test rule content.")

    result = runner.invoke(cli, ["view", str(tmp_path)])
    assert result.exit_code == 0
    # Check for key phrases from the output, less sensitive to exact panel formatting
    assert "Information for Workspace" in result.output
    assert Path(tmp_path).name in result.output # Check for directory name
    assert "Detailed MCP Information" in result.output
    assert "AllFeatures App MCPs:" in result.output # From MockAppAllFeatures
    assert "Rules for" in result.output
    assert Path(tmp_path).name in result.output # Check for directory name
    assert "AllFeatures App Rules:" in result.output
    assert "allfeatures.rules.md" in result.output # Workspace rule
    assert "global.md" in result.output

def test_agapps_view_workspace_path_valid_app_filter(runner: CliRunner, tmp_path: Path):
    """Test `agapps view <WORKSPACE_PATH> --app <APP_NAME>`."""
    result = runner.invoke(cli, ["view", str(tmp_path), "--app", "no-mcps"])
    assert result.exit_code == 0
    assert "Filtered by App: no-mcps" in result.output
    assert "Information for Workspace" in result.output # Main title should still be there
    assert Path(tmp_path).name in result.output # Check for directory name
    assert "Detailed MCP Information" not in result.output
    assert "No MCP configurations found for" in result.output
    assert "no-mcps" in result.output
    assert "in" in result.output
    assert Path(tmp_path).name in result.output
    assert "Rules for" in result.output
    assert Path(tmp_path).name in result.output # Check for directory name
    assert "NoMCPs App Rules:" in result.output
    assert "AllFeatures App" not in result.output # Should be filtered out

def test_agapps_view_workspace_path_invalid_non_existent(runner: CliRunner):
    """Test `agapps view <WORKSPACE_PATH>` with a non-existent path."""
    result = runner.invoke(cli, ["view", "/path/to/non_existent_dir"])
    assert result.exit_code != 0 # Click usually exits with 2 for bad param
    assert "Error: Invalid value for 'WORKSPACE_PATH': Directory '/path/to/non_existent_dir' does not exist." in result.output

def test_agapps_view_workspace_path_invalid_is_file(runner: CliRunner, tmp_path: Path):
    """Test `agapps view <WORKSPACE_PATH>` with a path that is a file."""
    file_path = tmp_path / "a_file.txt"
    file_path.touch()
    result = runner.invoke(cli, ["view", str(file_path)])
    assert result.exit_code != 0 # Click usually exits with 2 for bad param
    assert f"Error: Invalid value for 'WORKSPACE_PATH': Directory '{str(file_path)}' is a file." in result.output

# --- `agapps mcps` tests ---

def test_agapps_mcps_summary(runner: CliRunner):
    """Test `agapps mcps` summary view."""
    result = runner.invoke(cli, ["mcps"])
    assert result.exit_code == 0
    assert "MCP Configurations" in result.output # Panel title for summary
    assert "AllFeatures App" in result.output
    assert "test_mcp" in result.output # MCP name from AllFeatures
    assert "NoMCPs App" in result.output # App name still listed
    # Check for ✓ symbol for apps with MCPs
    # AllFeatures App | test_mcp (✓) | another_mcp () | ws_mcp ()
    # NoMCPs App      |              |                |
    # NoGlobalRules App |              | ✓              |
    # NoWorkspaceRules App |         |                | ✓
    # This is tricky to assert perfectly without parsing tables.
    # A simpler check is that apps are listed and known MCPs are present in the table headers.
    assert "another_mcp" in result.output # MCP name from NoGlobalRules
    assert "ws_mcp" in result.output    # MCP name from NoWorkspaceRules

def test_agapps_mcps_details(runner: CliRunner):
    """Test `agapps mcps --details`."""
    result = runner.invoke(cli, ["mcps", "--details"])
    assert result.exit_code == 0
    assert "Detailed MCP Information" in result.output
    assert "AllFeatures App MCPs:" in result.output
    assert "test_mcp: do_something" in result.output
    assert "KEY = VALUE" in result.output # Corrected assertion for non-redacted short value
    assert "NoMCPs App" not in result.output # Should not show details for apps with no MCPs
    assert "NoGlobalRules App MCPs:" in result.output # This app has MCPs
    assert "another_mcp: do_else" in result.output
    assert "NoWorkspaceRules App MCPs:" in result.output # This app has MCPs
    assert "ws_mcp: do_ws" in result.output
    assert "NoFeatures App" not in result.output # No MCPs

def test_agapps_mcps_filter_summary(runner: CliRunner):
    """Test `agapps mcps --app <APP_NAME>` summary view."""
    result = runner.invoke(cli, ["mcps", "--app", "all-features"])
    assert result.exit_code == 0
    assert "MCP Configurations" in result.output
    assert "AllFeatures App" in result.output
    assert "test_mcp" in result.output # MCP for all-features
    assert "NoMCPs App" not in result.output # Filtered out
    assert "another_mcp" not in result.output # MCP from other app

def test_agapps_mcps_filter_details(runner: CliRunner):
    """Test `agapps mcps --app <APP_NAME> --details`."""
    result = runner.invoke(cli, ["mcps", "--app", "all-features", "-d"])
    assert result.exit_code == 0
    assert "Detailed MCP Information" in result.output
    assert "AllFeatures App MCPs:" in result.output
    assert "test_mcp: do_something" in result.output
    assert "NoGlobalRules App MCPs:" not in result.output

def test_agapps_mcps_filter_no_mcps_app(runner: CliRunner):
    """Test `agapps mcps --app <APP_NAME>` for an app with no MCPs."""
    result = runner.invoke(cli, ["mcps", "--app", "no-mcps"])
    assert result.exit_code == 0
    assert "No MCP configurations found for app 'no-mcps'" in result.output
    assert "Detailed MCP Information" not in result.output # If no summary, no details either

def test_agapps_mcps_filter_non_existent_app(runner: CliRunner):
    """Test `agapps mcps --app <NON_EXISTENT_APP>`."""
    result = runner.invoke(cli, ["mcps", "--app", "ghost-app"])
    assert result.exit_code == 0 # CLI currently handles this gracefully
    assert "Error: App 'ghost-app' not found." in result.output

# --- `agapps rules` tests ---

def test_agapps_rules_global_only(runner: CliRunner):
    """Test `agapps rules` (global rules only)."""
    result = runner.invoke(cli, ["rules"])
    assert result.exit_code == 0
    assert "Global Rules" in result.output # Panel title
    assert "AllFeatures App Rules:" in result.output
    assert "~/.config/allfeatures/global.md" in result.output
    # Check for the note about apps with no global rules
    assert "Note: NoGlobalRules App, NoFeatures App do not have any global rules configured." in result.output
    assert "NoGlobalRules App Rules:" not in result.output # Explicitly check it's NOT there
    assert "NoWorkspaceRules App Rules:" in result.output
    assert "~/.config/nows/global.md" in result.output
    assert "Workspace rules:" not in result.output # No workspace path given

def test_agapps_rules_with_workspace(runner: CliRunner, tmp_path: Path):
    """Test `agapps rules <WORKSPACE_PATH>`."""
    (tmp_path / "allfeatures.rules.md").write_text("ws content for allfeatures")
    (tmp_path / "noglobal.rules.md").write_text("ws content for noglobal")

    result = runner.invoke(cli, ["rules", str(tmp_path)])
    assert result.exit_code == 0
    # Check for key parts of the title, robust to panel formatting
    assert "Rules for" in result.output
    assert Path(tmp_path).name in result.output # Check for directory name
    
    assert "AllFeatures App Rules:" in result.output
    assert "~/.config/allfeatures/global.md" in result.output # Global
    # Check for the file path in a way that's robust to line breaks
    assert "allfeatures.rules.md" in result.output
    assert "(4 words, 1 lines)" in result.output

    assert "NoGlobalRules App Rules:" in result.output # This app has workspace rules
    assert "noglobal.rules.md" in result.output # Workspace filename
    assert "(4 words, 1 lines)" in result.output # File content info
    assert "No global rules found" in result.output # for NoGlobalRules App

    assert "NoMCPs App Rules:" in result.output # Has global and workspace rules
    assert "~/.config/nomcps/global.md" in result.output
    # Need to create the workspace rule file for NoMCPs App if we want to assert its content
    (tmp_path / "nomcps.rules.md").write_text("ws content for nomcps")
    # Re-invoke if file creation is after first invoke, or ensure all files created before invoke.
    # For simplicity, let's assume files are created before relevant assertions or sections are checked.
    # However, the test structure runs invoke once. So, create all files first.
    result_after_nomcps_ws_created = runner.invoke(cli, ["rules", str(tmp_path)]) # Re-invoke if needed, or create before.
                                                                                # Let's create it before the main invoke for this test.
    assert "nomcps.rules.md" in result_after_nomcps_ws_created.output


def test_agapps_rules_filter_global(runner: CliRunner):
    """Test `agapps rules --app <APP_NAME>` (global rules)."""
    result = runner.invoke(cli, ["rules", "--app", "all-features"])
    assert result.exit_code == 0
    assert "Global Rules" in result.output
    assert "AllFeatures App Rules:" in result.output
    assert "~/.config/allfeatures/global.md" in result.output
    assert "NoMCPs App Rules:" not in result.output

def test_agapps_rules_filter_workspace(runner: CliRunner, tmp_path: Path):
    """Test `agapps rules <WORKSPACE_PATH> --app <APP_NAME>`."""
    (tmp_path / "nomcps.rules.md").write_text("ws content for nomcps")

    result = runner.invoke(cli, ["rules", str(tmp_path), "--app", "no-mcps"])
    assert result.exit_code == 0
    assert "Filtered by App: no-mcps" in result.output
    assert "Rules for" in result.output
    assert Path(tmp_path).name in result.output # Check for directory name
    assert "NoMCPs App Rules:" in result.output
    assert "~/.config/nomcps/global.md" in result.output
    # More robust assertion checking that the file path is somewhere in the output
    # rather than requiring an exact format, as the path might be split across lines
    assert "nomcps.rules.md" in result.output
    assert "(4 words, 1 lines)" in result.output
    assert "AllFeatures App" not in result.output

def test_agapps_rules_filter_non_existent_app(runner: CliRunner):
    """Test `agapps rules --app <NON_EXISTENT_APP>`."""
    result = runner.invoke(cli, ["rules", "--app", "ghost-app"])
    assert result.exit_code == 0
    assert "Error: App 'ghost-app' not found." in result.output

def test_agapps_rules_no_rules_app(runner: CliRunner, tmp_path: Path):
    """Test `agapps rules` when an app has no rules at all."""
    result_global = runner.invoke(cli, ["rules", "--app", "no-features"])
    assert result_global.exit_code == 0
    assert "No rules found for app 'no-features' globally" in result_global.output

    result_workspace = runner.invoke(cli, ["rules", str(tmp_path), "--app", "no-features"])
    assert result_workspace.exit_code == 0
    # Check for the specific message within the output, robust to panel formatting
    assert "No rules found for app 'no-features'" in result_workspace.output
    assert Path(tmp_path).name in result_workspace.output # ensure context is mentioned (directory name)
    assert "or globally" in result_workspace.output

def test_agapps_rules_invalid_workspace_path(runner: CliRunner):
    """Test `agapps rules <INVALID_PATH>`."""
    result = runner.invoke(cli, ["rules", "/path/to/non_existent_dir_for_rules"])
    assert result.exit_code != 0 # Should be 2 for bad parameter
    assert "Error: Invalid value for '[WORKSPACE_PATH]': Directory '/path/to/non_existent_dir_for_rules' does not exist." in result.output


# It's important that the mock_apps_dict fixture correctly restores CLI_APPS
# to avoid interference if other test files were to import agapps.cli.APPS directly.
# For a single test file, this setup should be robust. 