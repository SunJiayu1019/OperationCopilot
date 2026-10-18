from pathlib import Path

from app.services.rag import KnowledgeLoader, VectorIndex


def test_loader_splits_markdown_and_search_returns_source_and_score(tmp_path: Path):
    source = tmp_path / "brand.md"
    source.write_text("# 品牌语气\n\n使用真实、轻量的表达。\n\n# 禁用词\n\n避免绝对化承诺。", encoding="utf-8")

    chunks = KnowledgeLoader().load_file(source, "brand")
    index = VectorIndex()
    index.add(chunks)
    hits = index.search("真实表达和绝对化承诺", top_k=2)

    assert len(chunks) == 2
    assert len(hits) == 2
    assert hits[0].collection == "brand"
    assert hits[0].source == "brand.md"
    assert 0 <= hits[0].score <= 1


def test_search_empty_index_returns_empty_list():
    assert VectorIndex().search("小红书规则") == []


def test_search_unknown_term_does_not_fabricate_evidence():
    index = VectorIndex()
    index.add([KnowledgeLoader().load_file(Path(__file__).parents[1] / "knowledge" / "brand" / "voice.md", "brand")[0]])
    assert index.search("宇宙飞船量子引擎") == []


def test_loader_splits_paragraphs_within_same_heading(tmp_path: Path):
    source = tmp_path / "rules.md"
    source.write_text("# 审核规则\n\n避免绝对化用语。\n\n不要编造配料。", encoding="utf-8")
    chunks = KnowledgeLoader().load_file(source, "platform")
    assert [chunk.text for chunk in chunks] == ["避免绝对化用语。", "不要编造配料。"]
    assert [chunk.heading for chunk in chunks] == ["审核规则", "审核规则"]
