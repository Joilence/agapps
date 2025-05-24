# agapps

A command-line tool for viewing (in the future perhaps managing) AI agent app configurations (MCPs, rules both global and local).

## Installation

```bash
# Install with uv (wip for pypi)
uv tool install --from https://github.com/Joilence/agapps.git

# Run the tool
agapps --help
```

## Usage

The `agapps` CLI provides several commands to inspect agent app configurations:

<details>
<summary>View Agent App Overview (Default Action)</summary>

**Command:** `agapps` or `agapps list`

**Description:** Lists all installed agent apps and their general capabilities, such as whether they support global rules, workspace rules, and MCP configurations.

**Example:**

```bash
$ agapps
╭──────────────────────╮
│ Installed Agent Apps │
╰──────────────────────╯
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ App              ┃ Global Rules ┃ Workspace Rules ┃ MCP Support ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ Claude Code      │ Yes          │ Yes             │ Yes         │
│ Claude Desktop   │ No           │ No              │ Yes         │
│ OpenAI Codex CLI │ Yes          │ Yes             │ No          │
│ Cursor           │ No           │ Yes             │ Yes         │
│ GitHub Copilot   │ No           │ Yes             │ No          │
│ Windsurf         │ Yes          │ Yes             │ Yes         │
└──────────────────┴──────────────┴─────────────────┴─────────────┘
Use 'agapps mcps' to view MCP configurations.
Use 'agapps rules' to view global and workspace rules.
Use 'agapps view <path>' to view combined MCP and Rule info for a workspace.
```

</details>

<details>
<summary>View Combined Workspace Information</summary>

**Command:** `agapps view <WORKSPACE_PATH>`

**Description:** Displays combined MCP (Model Context Protocol) and Rule information for the specified `<WORKSPACE_PATH>`. This view automatically shows detailed MCP information.

**Options:**

- `--app <APP_NAME>`: Filter the displayed MCP and Rule information by the specified app.

**Examples:**

- Show info for the current directory:

  ```bash
  $ agapps view .
  ╭──────────────────────────────╮
  │ Information for Workspace: . │
  ╰──────────────────────────────╯
  ╭──────────────────────────╮
  │ Detailed MCP Information │
  ╰──────────────────────────╯
  Claude Code MCPs:
    Source: ~/Library/Application\ Support/Claude/claude_desktop_config.json
    • filesystem: npx -y @modelcontextprotocol/server-filesystem /path/to/project-feat-branch
    # ... (other MCPs and Apps truncated for brevity) ...
  ╭─────────────╮
  │ Rules for . │
  ╰─────────────╯
    Claude Code Rules:
      Global rules:
      • ~/.claude/CLAUDE.md (201 words, 20 lines)
      No workspace rules found in ..
    OpenAI Codex CLI Rules:
      Global rules:
      • ~/.codex/AGENTS.md (134 words, 10 lines)
      No workspace rules found in ..
    Cursor Rules:
      No global rules found.
      Workspace rules for .:
      • .cursor/rules/project-rules.mdc (113 words, 22 lines)
    GitHub Copilot Rules:
      No global rules found.
      Workspace rules for .:
      • .github/copilot-instructions.md (260 words, 50 lines)
    # ... (other rules truncated for brevity) ...
  ```

- Show info for a specific project path:

  ```bash
  agapps view /path/to/your/project
  ```

- Show info for the current directory, filtered by the `cursor` app:

  ```bash
  agapps view . --app cursor
  ```

</details>

<details>
<summary>List MCP Configurations</summary>

**Command:** `agapps mcps`

**Description:** Lists MCP (Model Context Protocol) configurations from all supported agent apps. By default, it shows a summary table.

**Options:**

- `--app <APP_NAME>`: Filter MCP configurations to show only those for the specified app.
- `--details` (or `-d`): Show detailed MCP information, including command strings and environment variables (sensitive values are masked).

**Examples:**

- Show MCP summary for all apps:

  ```bash
  $ agapps mcps
  ╭────────────────────╮
  │ MCP Configurations │
  ╰────────────────────╯
  ┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┓
  ┃ App              ┃ filesystem ┃ memory    ┃ notion    ┃
  ┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━┩
  │ Claude Code      │ ✓          │ ✓ (1 env) │ ✓ (1 env) │
  │ Claude Desktop   │ ✓          │ ✓ (1 env) │ ✓ (1 env) │
  │ Windsurf         │            │           │           │
  │ Cursor           │            │           │           │
  │ OpenAI Codex CLI │            │           │           │
  └──────────────────┴────────────┴───────────┴───────────┘
  ```

- Show MCP summary for Cursor:

  ```bash
  agapps mcps --app cursor
  ```

- Show detailed MCP information for all apps:

  ```bash
  $ agapps mcps --details
  ╭──────────────────────────╮
  │ Detailed MCP Information │
  ╰──────────────────────────╯
  Claude Code MCPs:
    Source: ~/Library/Application\ Support/Claude/claude_desktop_config.json
    • filesystem: npx -y @modelcontextprotocol/server-filesystem /path/to/project-feat-branch
    • memory: npx -y @modelcontextprotocol/server-memory
      MEMORY_FILE_PATH = ~/mcp-server-memory.json
    • notion: node /path/to/mcp-notion-server/notion/build/index.js
      NOTION_API_TOKEN = ntn_****v0fF
  # ... (other app details would follow)
  ```

- Show detailed MCP information for Windsurf:

  ```bash
  agapps mcps --app windsurf -d
  ```

</details>

<details>
<summary>List Rules</summary>

**Command:** `agapps rules [WORKSPACE_PATH]`

**Description:** Lists rules from supported agent apps.

- If no `WORKSPACE_PATH` is provided, it lists only global rules for all apps (or a specific app if filtered).
- If a `WORKSPACE_PATH` is provided, it lists both global rules and rules specific to that workspace for all apps (or a specific app if filtered).

**Options:**

- `--app <APP_NAME>`: Filter rules to show only those for the specified app.

**Examples:**

- Show global rules for all apps:

  ```bash
  $ agapps rules
  ╭──────────────╮
  │ Global Rules │
  ╰──────────────╯
  Claude Code Rules:
    Global rules:
    • ~/.claude/CLAUDE.md (201 words, 20 lines)
  OpenAI Codex CLI Rules:
    Global rules:
    • ~/.codex/AGENTS.md (134 words, 10 lines)
  Windsurf Rules:
    Global rules:
    • ~/.codeium/windsurf/memories/global_rules.md (124 words, 9 lines)
  Note: Claude Desktop, Cursor do not have any global rules configured.
  ```

- Show global and current directory's workspace rules for all apps:

  ```bash
  $ agapps rules .
  ╭──────────────────────────────────────────────────────────╮
  │ Rules for . (workspace) and Global Rules                 │
  ╰──────────────────────────────────────────────────────────╯
  Claude Code Rules:
    Global rules:
    • ~/.claude/CLAUDE.md (201 words, 20 lines)
    No workspace rules found in ..
  OpenAI Codex CLI Rules:
    Global rules:
    • ~/.codex/AGENTS.md (134 words, 10 lines)
    No workspace rules found in ..
  Cursor Rules:
    No global rules found.
    Workspace rules for .:
    • .cursor/rules/project-rules.mdc (113 words, 22 lines)
  Windsurf Rules:
    Global rules:
    • ~/.codeium/windsurf/memories/global_rules.md (124 words, 9 lines)
    No workspace rules found in ..
  Note: Claude Desktop does not have any rules configured for this workspace or globally.
  ```

- Show global rules for OpenAI Codex CLI:

  ```bash
  agapps rules --app codex-cli
  ```

- Show global and project-specific rules for Cursor in `/path/to/project`:

  ```bash
  agapps rules /path/to/project --app cursor
  ```

</details>

You can also use `agapps --help` or `agapps <subcommand> --help` (e.g., `agapps mcps --help`) for more detailed help directly from the CLI.

## How it Works

Each supported agent app (e.g., `ClaudeCode`, `Cursor`) implements the `AgentApp` interface from `agapps.schema`. This interface defines methods for retrieving:

- **MCP Configurations**: Loaded from app-specific configuration files (e.g., `~/.cursor/mcp.json`). The tool parses these files to extract server names, commands, and environment variables.
- **Global Rules**: General instructions or preferences for the agent, usually stored in the user's home directory (e.g., `~/.claude/CLAUDE.md`).
- **Workspace Rules**: Project-specific instructions, often found in the project root or a dedicated directory (e.g., `.cursor/rules/`).

The `agapps` CLI aggregates this information and presents it in a user-friendly format, using tables and clear distinctions between global and workspace contexts.

<details>
<summary>Supported Agent Apps</summary>

- **Claude Code**
  - **MCP Config**: `claude_desktop_config.json` (platform-specific, e.g., `~/Library/Application Support/Claude/`)
  - **Global Rules**: `~/.claude/CLAUDE.md`
  - **Workspace Rules**:
    - `CLAUDE.md`
    - `CLAUDE.local.md`
- **Claude Desktop**
  - **MCP Config**: `claude_desktop_config.json` (platform-specific)
  - **Global Rules**: Not supported.
  - **Workspace Rules**: Not supported.
- [**OpenAI Codex CLI**](https://github.com/openai/codex/)
  - **MCP Config**: Not supported (client only).
  - **Global Rules**: `~/.codex/AGENTS.md`
  - **Workspace Rules**:
    - `AGENTS.md`
- **Cursor**
  - **MCP Config**: `~/.cursor/mcp.json`
  - **Global Rules**: `~/.cursor/global_rules.md`
  - **Workspace Rules**:
    - `.cursorrules` (deprecated, single file)
    - `.cursor/rules/*.md` (multi-file)
- **GitHub Copilot**
  - **MCP Config**: Not supported.
  - **Global Rules**: Not supported.
  - **Workspace Rules**:
    - `.github/copilot-instructions.md` (repository custom instructions)
    - `.github/prompts/*.prompt.md` (prompt files for VS Code)
- **Windsurf**
  - **MCP Config**:
    - `~/.codeium/windsurf/mcp_config.json`
  - **Global Rules**:
    - `~/.codeium/windsurf/memories/*.md`
  - **Workspace Rules**:
    - `.windsurfrules` (deprecated, single file)
    - `.windsurf/rules/*.md` (multi-file)

</details>

## Development

To set up the development environment:

```bash
git clone https://github.com/Joilence/agapps.git
cd agapps
# setup venv
uv sync
# install editable agapps
uv tool install agapps --with-editable .
```

### Update paths

If an agent app changes its configuration file paths or rule locations:

1. **Locate the app's module** in `src/agapps/agent_apps/` (e.g., `cursor.py`).
2. **Update path attributes** in its `__init__` method (e.g., `self.global_rules_path`).
3. **Adjust logic** in methods like `get_mcps()`, `get_global_rules()`, or `get_workspace_rules()` if file names or directory structures have changed significantly.
4. **Update the `README.md`**: Modify the paths listed for that app under the "Supported Agent Apps" section to reflect the changes.

### Support more agent apps

To add support for a new agent app:

1. **Create a new Python module** in `src/agapps/agent_apps/` (e.g., `my_new_app.py`).
2. **Define a class** in this module that inherits from `agapps.schema.AgentApp`.

   ```python
   from agapps.schema import AgentApp, MCP, Rule
   from pathlib import Path
   from typing import List, Union

   class MyNewApp(AgentApp):
       def __init__(self):
           super().__init__(name="My New App")
           # Initialize paths to config files, rule files, etc.

       def get_mcps(self) -> List[MCP]:
           # Logic to find and parse MCP configurations
           return []

       def get_mcp_config_paths(self) -> List[Path]:
           # Logic to return paths to MCP configuration files
           return []

       def get_global_rules(self) -> List[Rule]:
           # Logic to find global rules
           return []

       def get_workspace_rules(self, workspace: Union[Path, str]) -> List[Rule]:
           # Logic to find workspace-specific rules
           return []
   ```

3. **Implement the methods** to locate and parse its specific configuration files for MCPs and rules.
4. **Register the new app** in both `src/agapps/agent_apps/__init__.py` and `src/agapps/cli.py`:
   - In `src/agapps/agent_apps/__init__.py`:
     - Import your new class: `from agapps.agent_apps.my_new_app import MyNewApp`
     - Add it to the `__all__` list: `__all__ = [..., "MyNewApp", ...]`
   - In `src/agapps/cli.py`:
     - Import your new class: `from agapps.agent_apps.my_new_app import MyNewApp`
     - Add it to the `APPS` dictionary: `APPS["my-new-app"] = MyNewApp`
