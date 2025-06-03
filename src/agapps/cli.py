import click
from pathlib import Path
from typing import Dict, List, Optional, Type, Any
import os
import re
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from agapps.agent_apps.claude_code import ClaudeCode
from agapps.agent_apps.claude_desktop import ClaudeDesktop
from agapps.agent_apps.codex_cli import CodexCli
from agapps.agent_apps.cursor import Cursor
from agapps.agent_apps.github_copilot import GitHubCopilot
from agapps.agent_apps.windsurf import Windsurf
from agapps.agent_apps.zed import Zed
from agapps.schema import Rule, AgentApp

# Map of app names to their classes
APPS: Dict[str, Type[AgentApp]] = {
    "claude-code": ClaudeCode,
    "claude-desktop": ClaudeDesktop,
    "codex-cli": CodexCli,
    "cursor": Cursor,
    "github-copilot": GitHubCopilot,
    "windsurf": Windsurf,
    "zed": Zed,
}

# Initialize Rich console
console = Console()


def print_rule_info(rule: Rule) -> None:
    """Format and print information about a rule."""
    try:
        with open(rule.pattern, "r") as f:
            content = f.read()
            lines = content.count("\n") + 1
            words = len(content.split())

        path_str = str(rule.pattern)
        home = str(Path.home())
        if path_str.startswith(home):
            rel_path = "~" + path_str[len(home) :]
        else:
            rel_path = path_str

        text = Text()
        text.append("    • ")
        text.append(rel_path, style="green")
        text.append(f" ({words} words, {lines} lines)")
        console.print(text)
    except (IOError, IsADirectoryError, FileNotFoundError):
        text = Text()
        text.append("    • ")
        text.append(str(rule.pattern), style="yellow")
        text.append(" (file not readable)")
        console.print(text)


def mask_sensitive_value(value: str) -> str:
    """
    Mask sensitive values, showing only first 4 and last 4 characters.
    Skip masking URLs, file paths, and non-sensitive values.
    """
    if not value or len(value) <= 8:
        return value

    if value.startswith(("http://", "https://", "ftp://", "ssh://", "git@")):
        return value

    if (
        value.startswith(("/", "~/", "."))
        or re.match(r"^[A-Za-z]:\\", value)
        or re.match(r"^/[A-Za-z]/Users/", value)
    ):
        return value

    if re.match(r"^[0-9]+(\.[0-9]+)?$", value):
        return value

    non_sensitive_values = [
        "true",
        "false",
        "yes",
        "no",
        "medium",
        "high",
        "low",
        "claude",
        "sonar",
        "gpt",
        "debug",
        "production",
        "development",
    ]
    if value.lower() in non_sensitive_values:
        return value

    return value[:4] + "****" + value[-4:]


def _display_mcp_summary_table(
    console_obj: Console,
    target_apps: Dict[str, Type[AgentApp]],
    app_mcps_data: Dict[str, List[Any]],
    app_mcp_counts: Dict[str, int],
    title_override: Optional[str] = None,
) -> None:
    """Helper to display the MCP summary table(s)."""
    all_mcp_names_summary = set()
    for mcp_list in app_mcps_data.values():
        for mcp in mcp_list:
            all_mcp_names_summary.add(mcp.name)

    if not all_mcp_names_summary:
        return

    all_mcp_names_summary = sorted(list(all_mcp_names_summary))
    panel_title = title_override if title_override else "MCP Configurations"
    console_obj.print(Panel.fit(panel_title, style="bold"))

    chunk_size = 4
    for i in range(0, len(all_mcp_names_summary), chunk_size):
        current_mcp_chunk = all_mcp_names_summary[i : i + chunk_size]
        table = Table(show_header=True)
        table.add_column("App")
        for mcp_name in current_mcp_chunk:
            table.add_column(mcp_name)

        sorted_apps_list = sorted(
            target_apps.items(),
            key=lambda app_item: app_mcp_counts.get(app_item[1]().name, 0),
            reverse=True,
        )

        for app_name_key, app_class in sorted_apps_list:
            app_instance = app_class()
            row_data = [app_instance.name]
            mcps_by_name = {
                mcp.name: mcp for mcp in app_mcps_data.get(app_instance.name, [])
            }
            for mcp_name_in_chunk in current_mcp_chunk:
                if mcp_name_in_chunk in mcps_by_name:
                    mcp = mcps_by_name[mcp_name_in_chunk]
                    if mcp.envs:
                        num_envs = len(mcp.envs)
                        row_data.append(f"✓ ({num_envs} env)")
                    else:
                        row_data.append("✓")
                else:
                    row_data.append("")
            table.add_row(*row_data)
        console_obj.print(table)
        if i + chunk_size < len(all_mcp_names_summary):
            console_obj.print()


def _render_mcp_info(
    console_obj: Console,
    app_filter: Optional[str],
    details: bool,
    for_workspace_path: Optional[str] = None,
) -> None:
    """Core logic to gather and display MCP information."""
    target_apps_to_display = APPS
    if app_filter:
        if app_filter not in APPS:
            console_obj.print(
                f"[red]Error:[/red] App '{app_filter}' not found. Available apps: {', '.join(APPS.keys())}"
            )
            return
        target_apps_to_display = {app_filter: APPS[app_filter]}

    gathered_app_mcps = {}
    gathered_app_mcp_counts = {}
    gathered_app_mcp_config_paths = {}
    any_mcps_found_for_any_target_app = False

    for app_name_iter, app_class_iter in target_apps_to_display.items():
        app_instance_iter = app_class_iter()
        mcp_configs = app_instance_iter.get_mcps(workspace=for_workspace_path)

        all_mcps = []
        all_config_paths = []

        if mcp_configs is not None:
            for config in mcp_configs:
                all_mcps.extend(config.servers)
                all_config_paths.append(config.path)

        if all_mcps:
            any_mcps_found_for_any_target_app = True
            gathered_app_mcps[app_instance_iter.name] = all_mcps
            gathered_app_mcp_counts[app_instance_iter.name] = len(all_mcps)
            if all_config_paths:
                gathered_app_mcp_config_paths[app_instance_iter.name] = all_config_paths
        else:
            gathered_app_mcp_counts[app_instance_iter.name] = 0

    if not any_mcps_found_for_any_target_app:
        # Check if it's because apps don't support MCPs
        apps_checked = 0
        apps_no_support = 0
        for app_name, app_class in target_apps_to_display.items():
            app_instance = app_class()
            apps_checked += 1
            if app_instance.get_mcps(workspace=for_workspace_path) is None:
                apps_no_support += 1

        if apps_checked > 0 and apps_checked == apps_no_support:
            if app_filter:
                console_obj.print(
                    f"\n[yellow]{app_filter} does not support MCP configurations.[/yellow]"
                )
            else:
                console_obj.print(
                    "\n[yellow]None of the selected apps support MCP configurations.[/yellow]"
                )
        else:
            if for_workspace_path:
                app_name_msg_part = f" for app '{app_filter}'" if app_filter else ""
                workspace_msg_part = (
                    f" in {for_workspace_path}" if for_workspace_path else ""
                )
                console_obj.print(
                    f"\n[yellow]No MCP configurations found{app_name_msg_part}{workspace_msg_part}.[/yellow]"
                )
            else:
                if app_filter:
                    console_obj.print(
                        f"\n[yellow]No MCP configurations found for app '{app_filter}'.[/yellow]"
                    )
                else:
                    console_obj.print(
                        "\n[yellow]No MCP configurations found in any app.[/yellow]"
                    )
        return

    if not for_workspace_path and not details:
        _display_mcp_summary_table(
            console_obj,
            target_apps_to_display,
            gathered_app_mcps,
            gathered_app_mcp_counts,
        )

    if details:
        console_obj.print(Panel.fit("Detailed MCP Information", style="bold"))
        any_details_shown = False
        for app_name_detail, app_class_detail in target_apps_to_display.items():
            app_instance_detail = app_class_detail()
            mcps_list_detail = gathered_app_mcps.get(app_instance_detail.name)

            if mcps_list_detail:
                any_details_shown = True
                console_obj.print(f"\n[bold]{app_instance_detail.name} MCPs:[/bold]")
                config_paths_detail = gathered_app_mcp_config_paths.get(
                    app_instance_detail.name, []
                )
                if config_paths_detail:
                    home_dir_str = str(Path.home())
                    formatted_paths = [
                        (
                            "~" + str(p)[len(home_dir_str) :]
                            if str(p).startswith(home_dir_str)
                            else str(p)
                        ).replace(" ", "\\ ")
                        for p in config_paths_detail
                    ]
                    paths_str = ", ".join(formatted_paths)
                    console_obj.print(f"  [dim]Source: {paths_str}[/dim]")

                for mcp_detail in mcps_list_detail:
                    console_obj.print(
                        f"  • [blue]{mcp_detail.name}[/blue]: {mcp_detail.command}"
                    )
                    if mcp_detail.envs:
                        for key, value in mcp_detail.envs.items():
                            masked_value = mask_sensitive_value(value)
                            console_obj.print(f"    {key} = {masked_value}")
        if not any_details_shown:
            if not for_workspace_path:
                console_obj.print(
                    "[yellow]No detailed MCP information to display for the selection.[/yellow]"
                )
            elif for_workspace_path and not any_mcps_found_for_any_target_app:
                # Check if it's because apps don't support MCPs
                apps_checked = 0
                apps_no_support = 0
                for app_name, app_class in target_apps_to_display.items():
                    app_instance = app_class()
                    apps_checked += 1
                    if app_instance.get_mcps(workspace=for_workspace_path) is None:
                        apps_no_support += 1

                if apps_checked > 0 and apps_checked == apps_no_support:
                    if app_filter:
                        console_obj.print(
                            f"[yellow]{app_filter} does not support MCP configurations.[/yellow]"
                        )
                    else:
                        console_obj.print(
                            "[yellow]None of the selected apps support MCP configurations.[/yellow]"
                        )
                else:
                    console_obj.print(
                        f"[yellow]No MCP configurations found for {app_filter if app_filter else 'any app'} in {for_workspace_path}.[/yellow]"
                    )


def _render_rules_info(
    console_obj: Console, app_filter: Optional[str], workspace_path_str: Optional[str]
) -> None:
    """Core logic to gather and display Rule information."""
    target_apps_to_display = APPS
    if app_filter:
        if app_filter not in APPS:
            console_obj.print(
                f"[red]Error:[/red] App '{app_filter}' not found. Available apps: {', '.join(APPS.keys())}"
            )
            return
        target_apps_to_display = {app_filter: APPS[app_filter]}
        console_obj.print(f"[dim]Filtered by App: {app_filter}[/dim]")
        console_obj.print()

    actual_workspace_path: Optional[Path] = (
        Path(workspace_path_str) if workspace_path_str else None
    )
    found_any_rules_at_all = False
    apps_no_support = []
    apps_no_configs = []

    title = "Global Rules"
    if actual_workspace_path:
        title = f"Rules for [green]{actual_workspace_path}[/green]"
    console_obj.print(Panel.fit(title, style="bold"))

    for app_name_iter, app_class_iter in target_apps_to_display.items():
        app_instance_iter = app_class_iter()
        rule_configs = app_instance_iter.get_rules(workspace=actual_workspace_path)

        # Check if app supports rules
        if rule_configs is None:
            apps_no_support.append(app_instance_iter.name)
            continue

        # Separate global and workspace rules
        global_rules_list = []
        workspace_rules_list = []

        for config in rule_configs:
            if config.type == "global":
                global_rules_list.extend(config.rules)
            elif config.type == "workspace":
                workspace_rules_list.extend(config.rules)

        if not global_rules_list and (
            not workspace_path_str or not workspace_rules_list
        ):
            apps_no_configs.append(app_instance_iter.name)
            continue

        found_any_rules_at_all = True
        console_obj.print(
            f"\n  [bold underline]{app_instance_iter.name} Rules:[/bold underline]"
        )

        if global_rules_list:
            console_obj.print("    Global rules:")
            for rule in global_rules_list:
                print_rule_info(rule)
        elif workspace_path_str:
            console_obj.print("    No global rules found.")
        elif not workspace_path_str and not workspace_rules_list:
            console_obj.print("    No global rules found.")

        if workspace_path_str:
            if workspace_rules_list:
                console_obj.print(
                    f"    Workspace rules for [green]{workspace_path_str}[/green]:"
                )
                for rule in workspace_rules_list:
                    print_rule_info(rule)
            else:
                console_obj.print(
                    f"    No workspace rules found in [green]{workspace_path_str}[/green]."
                )

        console_obj.print()

    if not found_any_rules_at_all:
        if actual_workspace_path:
            if app_filter:
                console_obj.print(
                    f"\n[yellow]No rules found for app '{app_filter}' in {actual_workspace_path} or globally.[/yellow]"
                )
            else:
                console_obj.print(
                    f"\n[yellow]No rules found for any app in {actual_workspace_path} or globally.[/yellow]"
                )
        elif app_filter:
            console_obj.print(
                f"\n[yellow]No rules found for app '{app_filter}' globally.[/yellow]"
            )
        else:
            console_obj.print("\n[yellow]No global rules found in any app.[/yellow]")

    # Show notes about apps without support or configs
    if (apps_no_support or apps_no_configs) and found_any_rules_at_all:
        # Apps that don't support rules
        if apps_no_support:
            conjunction = "does" if len(apps_no_support) == 1 else "do"
            apps_str = ", ".join(apps_no_support)
            console_obj.print(
                f"\n[dim]Note: {apps_str} {conjunction} not support rule configurations.[/dim]"
            )

        # Apps that support rules but have none configured
        if apps_no_configs:
            conjunction = "does" if len(apps_no_configs) == 1 else "do"
            apps_str = ", ".join(apps_no_configs)
            if workspace_path_str:
                console_obj.print(
                    f"\n[yellow]Note: {apps_str} {conjunction} not have any rules configured for this workspace or globally.[/yellow]"
                )
            else:
                console_obj.print(
                    f"\n[yellow]Note: {apps_str} {conjunction} not have any global rules configured.[/yellow]"
                )


def _render_prompts_info(
    console_obj: Console, app_filter: Optional[str], workspace_path_str: Optional[str]
) -> None:
    """Core logic to gather and display Prompt information."""
    target_apps_to_display = APPS
    if app_filter:
        if app_filter not in APPS:
            console_obj.print(
                f"[red]Error:[/red] App '{app_filter}' not found. Available apps: {', '.join(APPS.keys())}"
            )
            return
        target_apps_to_display = {app_filter: APPS[app_filter]}
        console_obj.print(f"[dim]Filtered by App: {app_filter}[/dim]")
        console_obj.print()

    actual_workspace_path: Optional[Path] = (
        Path(workspace_path_str) if workspace_path_str else None
    )
    found_any_prompts_at_all = False
    apps_no_support = []
    apps_no_configs = []

    title = "Global Prompts"
    if actual_workspace_path:
        title = f"Prompts for [green]{actual_workspace_path}[/green]"
    console_obj.print(Panel.fit(title, style="bold"))

    for app_name_iter, app_class_iter in target_apps_to_display.items():
        app_instance_iter = app_class_iter()
        prompt_configs = app_instance_iter.get_prompts(workspace=actual_workspace_path)

        # Check if app supports prompts
        if prompt_configs is None:
            apps_no_support.append(app_instance_iter.name)
            continue

        # Separate global and workspace prompts
        global_prompts_list = []
        workspace_prompts_list = []

        for config in prompt_configs:
            if config.type == "global":
                global_prompts_list.extend(config.prompts)
            elif config.type == "workspace":
                workspace_prompts_list.extend(config.prompts)

        if not global_prompts_list and (
            not workspace_path_str or not workspace_prompts_list
        ):
            apps_no_configs.append(app_instance_iter.name)
            continue

        found_any_prompts_at_all = True
        console_obj.print(
            f"\n  [bold underline]{app_instance_iter.name} Prompts:[/bold underline]"
        )

        if global_prompts_list:
            console_obj.print("    Global prompts:")
            for prompt in global_prompts_list:
                console_obj.print(
                    f"    • {prompt.pattern} ({prompt.word_count} words, {prompt.line_count} lines)"
                )
        elif workspace_path_str:
            console_obj.print("    No global prompts found.")
        elif not workspace_path_str and not workspace_prompts_list:
            console_obj.print("    No global prompts found.")

        if workspace_path_str:
            if workspace_prompts_list:
                console_obj.print(
                    f"    Workspace prompts for [green]{workspace_path_str}[/green]:"
                )
                for prompt in workspace_prompts_list:
                    console_obj.print(
                        f"    • {prompt.pattern} ({prompt.word_count} words, {prompt.line_count} lines)"
                    )
            else:
                console_obj.print(
                    f"    No workspace prompts found in [green]{workspace_path_str}[/green]."
                )

        console_obj.print()

    if not found_any_prompts_at_all:
        if actual_workspace_path:
            if app_filter:
                console_obj.print(
                    f"\n[yellow]No prompts found for app '{app_filter}' in {actual_workspace_path} or globally.[/yellow]"
                )
            else:
                console_obj.print(
                    f"\n[yellow]No prompts found for any app in {actual_workspace_path} or globally.[/yellow]"
                )
        elif app_filter:
            console_obj.print(
                f"\n[yellow]No prompts found for app '{app_filter}' globally.[/yellow]"
            )
        else:
            console_obj.print("\n[yellow]No global prompts found in any app.[/yellow]")

    # Show notes about apps without support or configs
    if (apps_no_support or apps_no_configs) and found_any_prompts_at_all:
        # Apps that don't support prompts
        if apps_no_support:
            conjunction = "does" if len(apps_no_support) == 1 else "do"
            apps_str = ", ".join(apps_no_support)
            console_obj.print(
                f"\n[dim]Note: {apps_str} {conjunction} not support prompt configurations.[/dim]"
            )

        # Apps that support prompts but have none configured
        if apps_no_configs:
            conjunction = "does" if len(apps_no_configs) == 1 else "do"
            apps_str = ", ".join(apps_no_configs)
            if workspace_path_str:
                console_obj.print(
                    f"\n[yellow]Note: {apps_str} {conjunction} not have any prompts configured for this workspace or globally.[/yellow]"
                )
            else:
                console_obj.print(
                    f"\n[yellow]Note: {apps_str} {conjunction} not have any global prompts configured.[/yellow]"
                )


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Agent Apps Manager (agapps) CLI.
    If run without subcommands, lists available apps."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(list_apps)


@cli.command("view")
@click.argument(
    "workspace_path",
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True),
)
@click.option("--app", "app_filter", help="Filter by app for workspace view.")
def view_workspace_info(workspace_path: str, app_filter: Optional[str]) -> None:
    """Display MCP and Rule information for a WORKSPACE_PATH."""
    console.print(
        Panel.fit(
            f"Information for Workspace: [green]{workspace_path}[/green]", style="bold"
        )
    )
    if app_filter:
        console.print(f"Filtered by App: [blue]{app_filter}[/blue]")

    _render_mcp_info(
        console, app_filter, details=True, for_workspace_path=workspace_path
    )
    console.print()
    _render_rules_info(console, app_filter, workspace_path)
    console.print()
    _render_prompts_info(console, app_filter, workspace_path)


@cli.command("list")
def list_apps() -> None:
    """List all installed agent apps and their general capabilities."""
    console.print(Panel.fit("Installed Agent Apps", style="bold"))

    table = Table(show_header=True)
    table.add_column("App")
    table.add_column("Global Rules")
    table.add_column("Workspace Rules")
    table.add_column("MCP Support")

    for app_name_key, app_class_type in APPS.items():
        app_instance_obj = app_class_type()

        # Check for global rules
        rule_configs = app_instance_obj.get_rules(workspace=None)
        has_global = "No"
        if rule_configs is not None:
            for config in rule_configs:
                if config.type == "global" and config.rules:
                    has_global = "Yes"
                    break

        # Check if app supports workspace rules using capability flags
        has_workspace = "Yes" if app_instance_obj.supports_workspace_rules else "No"

        # Check for MCP support using capability flags
        has_mcps = (
            "Yes"
            if (
                app_instance_obj.supports_global_mcps
                or app_instance_obj.supports_workspace_mcps
            )
            else "No"
        )

        table.add_row(app_instance_obj.name, has_global, has_workspace, has_mcps)

    console.print(table)
    console.print("\nUse [yellow]'agapps mcps'[/yellow] to view MCP configurations.")
    console.print(
        "Use [yellow]'agapps rules'[/yellow] to view global and workspace rules."
    )
    console.print(
        "Use [yellow]'agapps prompts'[/yellow] to view global and workspace prompts."
    )
    console.print(
        "Use [yellow]'agapps view <path>'[/yellow] to view combined MCP and Rule info for a workspace."
    )


@cli.command("mcps")
@click.option("--app", "app_filter", help="Filter MCPs by specific app.")
@click.option("--details", "-d", is_flag=True, help="Show detailed MCP information.")
def mcps_command(app_filter: Optional[str] = None, details: bool = False) -> None:
    """List MCP configurations from the supported apps."""
    _render_mcp_info(console, app_filter, details, for_workspace_path=None)


@cli.command("rules")
@click.option("--app", "app_filter", help="Filter rules by specific app.")
@click.argument(
    "workspace_path",
    required=False,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True),
)
def rules_command(
    app_filter: Optional[str] = None, workspace_path: Optional[str] = None
) -> None:
    """List rules from supported apps, optionally for a workspace."""
    _render_rules_info(console, app_filter, workspace_path)


@cli.command("prompts")
@click.option("--app", "app_filter", help="Filter prompts by specific app.")
@click.argument(
    "workspace_path",
    required=False,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True),
)
def prompts_command(
    app_filter: Optional[str] = None, workspace_path: Optional[str] = None
) -> None:
    """List prompts/custom commands from supported apps, optionally for a workspace."""
    _render_prompts_info(console, app_filter, workspace_path)


if __name__ == "__main__":
    os.environ["FORCE_COLOR"] = "1"
    cli()
