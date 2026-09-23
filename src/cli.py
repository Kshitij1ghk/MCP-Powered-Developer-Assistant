import sys
import os

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.prompt import Confirm
from rich.markdown import Markdown

from src.agent.orchestrator import AgentOrchestrator, AgentResponse
from src.config import ALLOWED_DIR

console = Console(highlight=False)

def cli_approval_callback(target_file: str, diff_text: str) -> bool:
    """
    Rich CLI Human-in-the-Loop Approval Callback:
    Displays syntax-highlighted diff preview and asks for explicit Y/N confirmation.
    """
    console.print("\n[bold yellow][!] HUMAN APPROVAL REQUIRED FOR CODE MODIFICATION[/bold yellow]")
    console.print(f"[bold cyan]Target File:[/bold cyan] {target_file}")
    
    # Render colored diff preview
    syntax = Syntax(diff_text, "diff", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title="[bold]Proposed Patch Diff Preview[/bold]", border_style="yellow"))

    # Interactive confirmation prompt
    try:
        confirmed = Confirm.ask("[bold green]Apply this patch to the workspace?[/bold green]", default=False)
        return confirmed
    except (KeyboardInterrupt, EOFError):
        console.print("\n[red]Operation cancelled by user.[/red]")
        return False

def render_agent_response(response: AgentResponse):
    """
    Renders tool execution flow and final answer using Rich components.
    """
    # 1. User Message
    console.print(Panel(f"[bold white]{response.user_query}[/bold white]", title="[bold blue]User Request[/bold blue]", border_style="blue"))

    # 2. Tools Called
    if response.tool_records:
        tool_table = Table(title="[MCP Tools Executed]", show_header=True, header_style="bold magenta", border_style="dim")
        tool_table.add_column("Step", style="dim", width=6)
        tool_table.add_column("MCP Tool", style="cyan", width=22)
        tool_table.add_column("Arguments", style="green")
        tool_table.add_column("Status", style="bold", width=10)

        for idx, rec in enumerate(response.tool_records, start=1):
            args_str = ", ".join(f"{k}='{v}'" for k, v in rec.arguments.items())
            if len(args_str) > 60:
                args_str = args_str[:57] + "..."
            
            # Status check
            res_val = rec.result
            success = True
            if isinstance(res_val, dict) and res_val.get("success") is False:
                success = False
            elif isinstance(res_val, dict) and "error" in res_val:
                success = False

            status_str = "[green]SUCCESS[/green]" if success else "[red]FAILED[/red]"
            tool_table.add_row(str(idx), rec.tool_name, args_str, status_str)

        console.print(tool_table)

    # 3. Final AI Response
    console.print(Panel(Markdown(response.final_answer), title="[bold green]AI Assistant Response[/bold green]", border_style="green"))
    console.print()

def start_interactive_cli():
    """Starts the interactive CLI developer loop."""
    console.print("[bold cyan]===========================================================[/bold cyan]")
    console.print("[bold white]   >> MCP-POWERED DEVELOPER ASSISTANT CLI[/bold white]")
    console.print(f"[dim]   Workspace Jail: {ALLOWED_DIR}[/dim]")
    console.print("[dim]   Type 'exit' or 'quit' to end session.[/dim]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]\n")

    orchestrator = AgentOrchestrator(approval_callback=cli_approval_callback)

    while True:
        try:
            query = console.input("[bold yellow]developer>[/bold yellow] ").strip()
            if not query:
                continue
            if query.lower() in ("exit", "quit"):
                console.print("[cyan]Goodbye![/cyan]")
                break

            response = orchestrator.run(query)
            render_agent_response(response)

        except (KeyboardInterrupt, EOFError):
            console.print("\n[cyan]Session ended.[/cyan]")
            break
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")

def main():
    if len(sys.argv) > 1:
        # Run one-off command
        query = " ".join(sys.argv[1:])
        orchestrator = AgentOrchestrator(approval_callback=cli_approval_callback)
        response = orchestrator.run(query)
        render_agent_response(response)
    else:
        start_interactive_cli()

if __name__ == "__main__":
    main()
