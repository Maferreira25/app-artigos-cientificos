import asyncio
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from pathlib import Path
from src.orchestrator import AcademicPipelineOrchestrator
from src.improver import AcademicPaperImprover
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
        console.print("[cyan]Iniciando orquestração autônoma com os modelos OpenRouter...[/cyan]")
        state = await orchestrator.executar_pipeline_completo(titulo=titulo, tema=tema)
        return state

    state = asyncio.run(_exec())

    table = Table(title="Resultado dos Quality Gates do Revisor Geral", show_header=True, header_style="bold magenta")
    table.add_column("Gate Avaliado", style="cyan")
    table.add_column("Status Decisão", style="bold")
    table.add_column("Score Global", justify="right")
    table.add_column("Autorizado?", justify="center")

    for gate_name, parecer in state.pareceres_gates.items():
        status_val = parecer.status_decisao.value
        status_color = "green" if status_val == "APROVADO" else ("yellow" if "RESSALVAS" in status_val else "red")
        table.add_row(
            gate_name,
            f"[{status_color}]{status_val}[/{status_color}]",
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
def improve(
    arquivo: Path = typer.Option(
        ...,
        "--arquivo", "-a",
        help="Caminho do arquivo do paper existente (.md, .txt ou .docx) a ser aprimorado",
        exists=True,
        readable=True
    ),
    titulo: Optional[str] = typer.Option(
        None,
        "--titulo", "-t",
        help="Título customizado para a obra (opcional, por padrão extrai do arquivo)"
    ),
    threshold: float = typer.Option(
        85.0,
        "--threshold",
        help="Nota de corte mínima da banca de examinadores (padrão 85.0)"
    )
):
    """Eleva um paper existente ao padrão de aprovação em banca examinadora de doutorado."""
    console.print(Panel.fit(
        f"[bold blue]Aprimoramento e Elevação de Paper para Banca de Doutorado[/bold blue]\n"
        f"Arquivo: [cyan]{arquivo}[/cyan]\n"
        f"Nota de Corte Mínima: [yellow]{threshold}/100[/yellow]",
        border_style="magenta"
    ))

    improver = AcademicPaperImprover(threshold=threshold)

    async def _exec():
        return await improver.aprimorar_paper(caminho_arquivo=arquivo, titulo_customizado=titulo)

    state, relatorio = asyncio.run(_exec())

    # Exibição do Painel da Banca
    diag = relatorio["diagnostico_inicial"]
    res = relatorio["resultado_final"]

    table = Table(title="Evolução Acadêmica para Banca Examinadora de Doutorado", show_header=True, header_style="bold cyan")
    table.add_column("Métrica de Avaliação", style="white")
    table.add_column("Pré-Intervenção", justify="center", style="yellow")
    table.add_column("Pós-Intervenção (Doutorado)", justify="center", style="bold green")

    table.add_row(
        "Score Médio dos Gates",
        f"{diag['score_medio']:.2f}/100",
        f"{res['score_medio_final']:.2f}/100"
    )
    table.add_row(
        "Inconsistências de Citação",
        str(diag["inconsistencias_citacao"]),
        str(res["inconsistencias_citacao_finais"])
    )
    table.add_row(
        "Veredito de Homologação",
        "PENDENTE DE DEFESA",
        "APROVADO COM LOUVOR" if res["homologado"] else "EXIGE AJUSTES"
    )

    console.print(table)

    console.print("\n[bold green]Documentos Gerados com Rigor de Doutorado:[/bold green]")
    console.print(f"- [cyan]Artigo Aprimorado (Markdown):[/cyan] {relatorio['artigo_md_path']}")
    if relatorio.get("artigo_docx_path"):
        console.print(f"- [cyan]Artigo Aprimorado (DOCX ABNT):[/cyan] {relatorio['artigo_docx_path']}")
    if relatorio.get("artigo_pdf_path"):
        console.print(f"- [cyan]Artigo Aprimorado (PDF ABNT):[/cyan] {relatorio['artigo_pdf_path']}")
    console.print(f"- [magenta]Dossiê da Banca Examinadora (Markdown):[/magenta] {relatorio['dossie_path']}")
    if relatorio.get("dossie_docx_path"):
        console.print(f"- [magenta]Dossiê da Banca Examinadora (DOCX):[/magenta] {relatorio['dossie_docx_path']}")
    if relatorio.get("dossie_pdf_path"):
        console.print(f"- [magenta]Dossiê da Banca Examinadora (PDF):[/magenta] {relatorio['dossie_pdf_path']}")

@app.command()
def web(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host para vincular o servidor web"),
    port: int = typer.Option(8000, "--port", "-p", help="Porta HTTP da interface web")
):
    """Inicia a Interface Web Editorial Stricto Sensu (FastAPI) para geração e aprimoramento de papers."""
    import uvicorn
    console.print(Panel.fit(
        f"[bold blue]Interface Web — Sistema Autônomo de Teses e Artigos de Doutorado[/bold blue]\n"
        f"Acesse no navegador: [bold green]http://{host}:{port}[/bold green]\n"
        f"Exportação ativa: [cyan]PDF ABNT Nativo + DOCX Pandoc + Markdown + Dossiê da Banca[/cyan]",
        border_style="green"
    ))
    uvicorn.run("src.web:app", host=host, port=port, reload=False)

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
    url: Optional[str] = typer.Option(None, "--url", help="URL do Servidor MCP (padrão: MCP_URL do .env)"),
    token: Optional[str] = typer.Option(None, "--token", help="Bearer Token MCP (padrão: MCP_BEARER_TOKEN do .env)"),
    tema: str = typer.Option("modulação de efeitos", "--tema", help="Tema jurídico para testar consulta remota")
):
    """Testa a conectividade com o servidor JurisprudênciaIA MCP."""
    from src.config import config
    target_url = url or config.mcp_url
    target_token = token or config.mcp_bearer_token
    console.print(f"[cyan]Conectando ao servidor MCP em {target_url}...[/cyan]")
    client = JurisprudenciaMcpClient(mcp_url=target_url, bearer_token=target_token, timeout=45.0)

    async def _test():
        try:
            res = await client.buscar_teses_vinculantes(tema)
            console.print("[green]Conexão MCP bem-sucedida![/green]")
            console.print(Panel(res[:600] + ("..." if len(res) > 600 else ""), title="Resposta MCP Oficial"))
        except Exception as e:
            console.print(f"[red]Falha na conexão com o servidor MCP: {e}[/red]")

    asyncio.run(_test())

if __name__ == "__main__":
    app()

