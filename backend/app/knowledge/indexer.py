"""Knowledge base indexer CLI — build/update ChromaDB from YAML files.

Usage:
    # Full rebuild
    python -m app.knowledge.indexer --kb-root ./knowledge_base --persist-dir ./data/chroma_db

    # Incremental (only changed files)
    python -m app.knowledge.indexer --incremental

    # With HuggingFace embeddings
    python -m app.knowledge.indexer --embedding-provider huggingface
"""

from pathlib import Path

import click
from dotenv import load_dotenv

# CLI entry: load .env so openai / openai_compatible can read env vars
load_dotenv()

from .embedder import KBEmbedder


@click.command()
@click.option(
    "--kb-root",
    default="./knowledge_base",
    help="Path to knowledge base root directory.",
)
@click.option(
    "--persist-dir",
    default="./data/chroma_db",
    help="Directory to persist ChromaDB index.",
)
@click.option(
    "--embedding-provider",
    default=None,
    type=click.Choice(["openai", "openai_compatible", "huggingface"]),
    help="Embedding provider (default: from KB_EMBEDDING_PROVIDER env).",
)
@click.option(
    "--incremental",
    is_flag=True,
    default=False,
    help="Incremental mode: only re-index changed/new/deleted files.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Scan files and report what would be indexed, without writing.",
)
def index_knowledge_base(
    kb_root: str = "./knowledge_base",
    persist_dir: str = "./data/chroma_db",
    embedding_provider: str = "openai",
    incremental: bool = False,
    dry_run: bool = False,
) -> None:
    """Build or update the vector index from YAML knowledge base files."""
    kb_path = Path(kb_root).resolve()
    persist_path = Path(persist_dir).resolve()

    if dry_run:
        click.echo(f"[dry-run] Would index from: {kb_path}")
        click.echo(f"[dry-run] Would persist to:  {persist_path}")
        click.echo(
            f"[dry-run] Mode:              {'incremental' if incremental else 'full rebuild'}"
        )

        # Count files without embedding
        loader = __import__("app.knowledge.loader", fromlist=["KnowledgeBaseLoader"])
        kb_loader = loader.KnowledgeBaseLoader(kb_path)
        methods = len(kb_loader.load_all_methods())
        papers = len(kb_loader.load_all_papers())
        templates = len(kb_loader.load_all_templates())
        problems = len(kb_loader.load_all_problems())
        click.echo(
            f"[dry-run] Files: {methods} methods + {papers} papers + "
            f"{templates} templates + {problems} problems "
            f"= {methods + papers + templates + problems} total"
        )
        return

    click.echo(f"Loading knowledge base from: {kb_path}")
    click.echo(f"Persisting index to:       {persist_path}")
    click.echo(f"Mode:                      {'incremental' if incremental else 'full rebuild'}")

    embedder = KBEmbedder(
        kb_root=kb_path,
        persist_dir=persist_path,
        embedding_provider=embedding_provider,
    )

    count = embedder.build_index(incremental=incremental)
    click.echo(f"\n[OK] Indexed {count} documents successfully.")


if __name__ == "__main__":
    index_knowledge_base()
