import coverage
import os
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

def generate_rich_report():
    console = Console()
    
    try:
        cov = coverage.Coverage()
        cov.load()
    except Exception as e:
        console.print("[bold red]Error: Could not load coverage database (.coverage).[/bold red]")
        console.print("[dim]Make sure to run your tests first with pytest.[/dim]")
        sys.exit(1)
        
    data = cov.get_data()
    if not data or not data.measured_files():
        console.print(Panel(
            "[bold red]No coverage data found in the .coverage database.[/bold red]\n"
            "Please run [cyan]pytest[/cyan] to execute tests and collect coverage.",
            title="Coverage Error",
            border_style="red"
        ))
        sys.exit(1)

    # Title panel
    console.print(Panel(
        Text.assemble(
            ("🧪 ", "bold yellow"),
            ("Amiga Reader - Colorized Test Coverage Report", "bold white"),
            ("\n", ""),
            ("Coverage metrics powered by ", "dim white"),
            ("coverage.py", "cyan"),
            (" & formatted with ", "dim white"),
            ("rich", "magenta")
        ),
        border_style="magenta",
        expand=False
    ))

    # Construct the table
    table = Table(
        title="[bold cyan]Code Coverage Metrics[/bold cyan]",
        border_style="bright_blue",
        header_style="bold bright_white"
    )
    
    table.add_column("File", style="cyan", header_style="bold cyan")
    table.add_column("Statements", justify="right", header_style="bold white")
    table.add_column("Missed", justify="right", header_style="bold red")
    table.add_column("Branches", justify="right", header_style="bold magenta")
    table.add_column("Partial Branches", justify="right", header_style="bold yellow")
    table.add_column("Cover", justify="right", header_style="bold green")
    table.add_column("Missing Lines", justify="left", header_style="bold red")
    
    total_stmts = 0
    total_miss = 0
    total_branches = 0
    total_missing_branches = 0
    total_partial_branches = 0
    
    # Process files
    measured_files = sorted(data.measured_files())
    # Track files already reported to prevent duplicate rows
    reported_files = set()
    
    for f in measured_files:
        # Resolve path
        # Normalize paths to handle relative/absolute mismatch
        rel_path = os.path.relpath(f, os.getcwd())
        if "src/amiga_reader" not in rel_path:
            continue
            
        if rel_path in reported_files:
            continue
        reported_files.add(rel_path)
            
        try:
            analysis = cov._analyze(f)
            numbers = analysis.numbers
            
            _, _, _, _, missing_formatted = cov.analysis2(f)
            
            # Extract statistics
            stmts = numbers.n_statements
            miss = numbers.n_missing
            branches = numbers.n_branches
            missing_branches = numbers.n_missing_branches
            partial_branches = numbers.n_partial_branches
            cover = numbers.pc_covered
            
            total_stmts += stmts
            total_miss += miss
            total_branches += branches
            total_missing_branches += missing_branches
            total_partial_branches += partial_branches
            
            # Format filename
            display_name = rel_path.replace("src/amiga_reader/", "")
            
            # Determine color-coded coverage percentage style
            if cover == 100:
                cover_style = "bold green"
            elif cover >= 90:
                cover_style = "bold yellow"
            else:
                cover_style = "bold red"
                
            cover_str = f"{cover:.1f}%"
            
            # Format misses and partials for aesthetics
            miss_str = f"[bold red]{miss}[/bold red]" if miss > 0 else "[dim white]0[/dim white]"
            branch_str = str(branches) if branches > 0 else "[dim]-[/dim]"
            partial_str = f"[bold yellow]{partial_branches}[/bold yellow]" if partial_branches > 0 else "[dim]-[/dim]"
            missing_str = f"[bold red]{missing_formatted}[/bold red]" if missing_formatted else ""
            
            table.add_row(
                display_name,
                str(stmts),
                miss_str,
                branch_str,
                partial_str,
                Text(cover_str, style=cover_style),
                missing_str
            )
        except Exception as e:
            continue
            
    # Calculate totals
    if total_stmts + total_branches > 0:
        overall_cover = (
            (total_stmts + total_branches - total_miss - total_partial_branches) 
            / (total_stmts + total_branches) 
            * 100.0
        )
    else:
        overall_cover = 100.0
        
    if overall_cover == 100:
        total_cover_style = "bold green"
    elif overall_cover >= 90:
        total_cover_style = "bold yellow"
    else:
        total_cover_style = "bold red"
        
    total_cover_str = f"{overall_cover:.1f}%"
    
    # Add summary total row
    table.add_section()
    table.add_row(
        "[bold white]TOTAL[/bold white]",
        f"[bold white]{total_stmts}[/bold white]",
        f"[bold red]{total_miss}[/bold red]" if total_miss > 0 else "0",
        f"[bold magenta]{total_branches}[/bold magenta]" if total_branches > 0 else "-",
        f"[bold yellow]{total_partial_branches}[/bold yellow]" if total_partial_branches > 0 else "-",
        Text(total_cover_str, style=total_cover_style),
        ""
    )
    
    console.print(table)
    console.print("\n[dim]Tip: Open [cyan]htmlcov/index.html[/cyan] for an interactive, line-by-line web report.[/dim]\n")

def main():
    generate_rich_report()

if __name__ == "__main__":
    main()
