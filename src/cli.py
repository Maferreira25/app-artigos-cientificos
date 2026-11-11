import asyncio
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from pathlib import Path
from src.orchestrator import AcademicPipelineOrchestrator
from src.exporter import AcademicExporter
from src.rag_store import RagStore
from src.mcp_client import JurisprudenciaMcpClient

app = typer.Typer(help="Pipeline Autônomo Local de Artigos e Teses de Doutorado com Integração MCP")
console = Console()

@app.command()
def run(
    titulo: str = typer.Option(
        "A Eficácia Vinculante dos Precedentes Judiciais no Direito Processual Brasileiro",
        "--titulo", "-t",
        help="Título da tese ou artigo acadêmico"
    ),
    tema: str = typer.Option(
        "Precedentes Vinculantes e Segurança Jurídica",
        "--tema", "-m",
        help="Tema ou questão central de pesquisa"
    ),
    threshold: float = typer.Option(
        85.0,
        "--threshold",
        help="Nota de corte mínima da Matriz Multidimensional (padrão 85.0)"
    )
):
    """Executa o pipeline autônomo completo governado pelos 6 Quality Gates."""
    console.print(Panel.fit(
        f"[bold blue]Pipeline Autônomo de Teses e Artigos Acadêmicos[/bold blue]\n"
        f"Título: [cyan]{titulo}[/cyan]\n"
        f"Tema: [magenta]{tema}[/magenta]\n"
        f"Limiar de Aprovação: [yellow]{threshold}/100[/yellow]",
        border_style="blue"
    ))

    async def _exec():
        orchestrator = AcademicPipelineOrchestrator(threshold=threshold)
        with console.status("[bold green]Executando agentes e Quality Gates..."):
            state = await orchestrator.executar_pipeline_completo(titulo=titulo, tema=tema)
        return state

    state = asyncio.run(_exec())

    table = Table(title="Resultado dos Quality Gates do Revisor Geral", show_header=True, header_style="bold magenta")
    table.add_column("Gate Avaliado", style="cyan")
    table.add_column("Status Decisão", style="bold")
    table.add_column("Score Global", justify="right")
    table.add_column("Autorizado?", justify="center")

    for gate_name, parecer in state.pareceres_gates.items():
        status_color = "green" if parecer.status_decisao == "APROVADO" else ("yellow" if "RESSALVAS" in parecer.status_decisao else "red")
        table.add_row(
            gate_name,
            f"[{status_color}]{parecer.status_decisao}[/{status_color}]",
            f"{parecer.score_global:.2f}",
            "✅" if parecer.autorizacao_avanco else "❌"
        )

    console.print(table)

    if state.status_geral == "HOMOLOGADO_SUCESSO":
        console.print("[bold green]✨ Todos os 6 Quality Gates foram Aprovados com Sucesso![/bold green]")
        exporter = AcademicExporter()
        md_path = exporter.gerar_markdown_consolidado(state)
        console.print(f"[bold cyan]Documento Markdown ABNT gerado em:[/bold cyan] {md_path}")
        
        docx_path = exporter.compilar_docx(md_path)
        if docx_path:
            console.print(f"[bold cyan]Documento DOCX compilado em:[/bold cyan] {docx_path}")
            
        pdf_path = exporter.compilar_pdf(md_path)
        if pdf_path:
            console.print(f"[bold cyan]Documento PDF compilado em:[/bold cyan] {pdf_path}")
    else:
        console.print(f"[bold red]⛔ O pipeline foi interrompido com status: {state.status_geral}[/bold red]")
        console.print("[yellow]Verifique as diretrizes de refatoração no parecer do Revisor Geral.[/yellow]")

@app.command()
def corpus():
    """Lista todos os precedentes e documentos autênticos salvos no corpus RAG local."""
    store = RagStore()
    docs = store.listar_documentos()
    
    table = Table(title=f"Corpus RAG Local ({len(docs)} documentos indexados)", show_header=True)
    table.add_column("Arquivo", style="cyan")
    table.add_column("Tipo", style="green")
    table.add_column("Tribunal", style="magenta")
    table.add_column("Processo / Título", style="white")

    for d in docs:
        meta = d["metadata"]
        table.add_row(
            d["file_name"],
            str(meta.get("tipo", "n/a")),
            str(meta.get("tribunal", "n/a")),
            str(meta.get("processo", meta.get("id", "n/a")))
        )

    console.print(table)

@app.command()
def test_mcp(
    url: str = typer.Option("http://localhost:8787", "--url", help="URL do Servidor MCP")
):
    """Testa a conectividade com o servidor JurisprudênciaIA MCP."""
    console.print(f"[cyan]Conectando ao servidor MCP em {url}...[/cyan]")
    client = JurisprudenciaMcpClient(mcp_url=url, timeout=10.0)

    async def _test():
        try:
            res = await client.call_tool("pesquisar_jurisprudencia", {"query": "teste"})
            console.print("[green]Conexão MCP bem-sucedida![/green]")
            console.print(Panel(res[:500] + ("..." if len(res) > 500 else ""), title="Resposta MCP"))
        except Exception as e:
            console.print(f"[red]Falha na conexão com o servidor MCP: {e}[/red]")

    asyncio.run(_test())

if __name__ == "__main__":
    app()
