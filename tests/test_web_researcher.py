import pytest
from src.web_researcher import AcademicWebResearcher
from src.schemas import ArtigoCientificoPesquisadoSchema

@pytest.mark.asyncio
async def test_web_researcher_reconstruir_abstract():
    researcher = AcademicWebResearcher()
    inverted = {"A": [0], "proteção": [1], "jurídica": [2]}
    abstract = researcher._reconstruir_abstract_openalex(inverted)
    assert abstract == "A proteção jurídica"

@pytest.mark.asyncio
async def test_web_researcher_sintese_markdown():
    artigos = [
        ArtigoCientificoPesquisadoSchema(
            titulo="A Proteção à Mulher na Jurisprudência do STJ",
            autores="Maria Berenice Dias",
            ano="2023",
            periodico_ou_repositorio="Revista dos Tribunais",
            doi_ou_url="https://doi.org/10.1234/exemplo",
            resumo_doutrinario="Estudo aprofundado sobre a autonomia das medidas protetivas.",
            fonte_pesquisa="openalex"
        )
    ]
    md = AcademicWebResearcher.sintetizar_corpus_web_em_markdown(artigos)
    assert "# Acervo de Doutrina e Artigos Científicos" in md
    assert "Maria Berenice Dias" in md
    assert "Revista dos Tribunais" in md
    assert "10.1234/exemplo" in md

@pytest.mark.asyncio
async def test_web_researcher_pesquisa_live_resiliente():
    researcher = AcademicWebResearcher(timeout=8.0)
    # Busca com termo acadêmico real
    artigos = await researcher.pesquisar_tudo("violencia domestica maria da penha", max_total=3)
    assert isinstance(artigos, list)
    # Se houver conexão de rede, deve retornar artigos com metadados
    if artigos:
        assert len(artigos) <= 3
        assert hasattr(artigos[0], "titulo")
        assert hasattr(artigos[0], "periodico_ou_repositorio")
