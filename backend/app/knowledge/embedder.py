"""ChromaDB embedding pipeline with incremental indexing support.

Build flow:
  build_index()              → full rebuild (clears existing DB)
  build_index(incremental=True) → hash-based incremental update
  add_document(path)         → index a single YAML file
  remove_document(doc_id)    → delete one document ID from the store
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from .loader import KnowledgeBaseLoader

# ── per-file hash tracking metadata file ────────────────────────────────

_HASH_DB = ".kb_index_hashes.json"


class KBEmbedder:
    """Build and manage ChromaDB vector index from knowledge base YAML files.

    Supports two modes:
      - Local: ChromaDB embedded in-process (persist_directory on disk)
      - Remote: ChromaDB HTTP server (e.g. Docker container), configured via
        CHROMA_HTTP_URL env var
    """

    _COLLECTION_NAME = "kb_docs"

    def __init__(
        self,
        kb_root: Path,
        persist_dir: Path,
        embedding_provider: str | None = None,
    ):
        from ..config import get_settings

        settings = get_settings()
        provider = embedding_provider or settings.kb_embedding_provider

        self.loader = KnowledgeBaseLoader(kb_root)
        self.kb_root = Path(kb_root)
        self.persist_dir = Path(persist_dir)
        self._hash_path = self.persist_dir / _HASH_DB
        self.embedding_provider = provider
        self.embeddings = None
        self._unavailable_reason = ""

        # Remote ChromaDB via HTTP (Docker container) — 独立进程，主进程省内存
        self._http_url = settings.chroma_http_url
        self._http_client = None

        if provider == "huggingface":
            from langchain_huggingface import HuggingFaceEmbeddings

            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
        elif provider == "openai":
            # 原生 OpenAI（需要 OPENAI_API_KEY）
            self.embeddings = OpenAIEmbeddings()
        else:
            # openai_compatible：任何 OpenAI 兼容 embedding 服务（SiliconFlow / 智谱 / DashScope 等）
            # Key 来源优先级：apikeys 页配置的 purpose=embedding Key > env 配置
            emb_key, emb_url, emb_model = self._resolve_embedding_config(settings)
            if emb_key:
                self.embeddings = OpenAIEmbeddings(
                    model=emb_model,
                    api_key=emb_key,
                    base_url=emb_url,
                )
            else:
                # 延迟失败：构造不报错，检索时自动回退关键词；reindex 时才提示
                self.embeddings = None
                self._unavailable_reason = (
                    "知识库 embedding 未配置：请在 /apikeys 页添加「向量」用途的 Key，"
                    "或在 backend/.env 设置 KB_EMBEDDING_API_KEY"
                )

    def _resolve_embedding_config(self, settings) -> tuple[str, str, str]:
        """解析 embedding 配置，返回 (api_key, base_url, model)。"""
        try:
            from ..api.apikeys import get_active_api_key

            emb = get_active_api_key("guest", purpose="embedding")
            if emb and emb.get("key"):
                return (
                    emb["key"],
                    emb.get("base_url") or settings.kb_embedding_base_url,
                    emb.get("model_name") or settings.kb_embedding_model,
                )
        except Exception:
            pass
        return (
            settings.kb_embedding_api_key,
            settings.kb_embedding_base_url,
            settings.kb_embedding_model,
        )

    # ── public: build ───────────────────────────────────────────────

    def build_index(self, incremental: bool = False) -> int:
        """Load YAML, chunk into Documents, embed, persist to ChromaDB.

        Args:
            incremental: If True, only re-index changed/new files and
                         remove documents whose source YAML was deleted.

        Returns:
            Total number of documents in the index after completion.
        """
        if self.embeddings is None:
            raise RuntimeError(
                self._unavailable_reason or "embedding 未配置，无法构建向量索引"
            )
        if incremental and self.persist_dir.exists():
            return self._incremental_update()
        else:
            return self._full_rebuild()

    def _full_rebuild(self) -> int:
        """Drop existing index and rebuild from scratch."""
        documents = self._all_yaml_to_documents()
        if not documents:
            return 0

        # Clean metadata (Chroma rejects empty lists)
        for doc in documents:
            doc.metadata = self._clean_metadata(doc.metadata)

        self.persist_dir.mkdir(parents=True, exist_ok=True)

        # Delete existing collection, then rebuild
        store = self._create_chroma()
        try:
            store.delete_collection()
        except Exception:
            pass  # collection may not exist yet

        # Create fresh store and add documents
        store = self._create_chroma()
        store.add_documents(documents)

        # Record hashes
        self._save_hashes(documents)
        return len(documents)

    # ── public: incremental update ──────────────────────────────────

    def _incremental_update(self) -> int:
        """Hash-based incremental re-index.

        Algorithm:
          1. Scan all YAML files → compute current hashes
          2. Compare with saved hashes → find changed / new / deleted
          3. Remove docs whose source files were deleted
          4. Remove stale docs whose source files changed
          5. Re-add docs for changed/new files
        """
        store = self.load_existing()
        docs_by_file, file_to_ids = self._scan_all_files()
        old_hashes = self._load_hashes()

        new_files: Dict[str, Set[str]] = {}  # path → {doc_id,...}
        changed_files: Dict[str, Set[str]] = {}
        deleted_sources: List[str] = []  # YAML paths that no longer exist
        deleted_ids: List[str] = []      # doc IDs to remove

        # Detect changes
        all_seen_ids: Set[str] = set()
        for yml_path, ids in file_to_ids.items():
            all_seen_ids.update(ids)
            old_hash = old_hashes.get(yml_path)
            new_hash = self._file_hash(Path(yml_path))
            if old_hash is None:
                new_files[yml_path] = ids
            elif old_hash != new_hash:
                changed_files[yml_path] = ids

        # Detect deletions: files in old_hashes but not on disk
        for old_path in old_hashes:
            if not Path(old_path).exists():
                deleted_sources.append(old_path)

        # Find old doc IDs associated with changed/deleted files
        stale_ids: Set[str] = set()
        stored_docs = old_hashes.get("__doc_ids__", {})
        if isinstance(stored_docs, dict):
            for old_path in list(changed_files.keys()) + deleted_sources:
                stale_ids.update(stored_docs.get(old_path, []))

        if not new_files and not changed_files and not deleted_sources:
            # Nothing changed — count existing docs
            try:
                collection = store._collection
                return collection.count()
            except Exception:
                return 0

        # Remove stale documents from changed/deleted files
        all_to_remove = list(stale_ids)
        if all_to_remove:
            try:
                store.delete(ids=all_to_remove)
            except Exception:
                pass  # ChromaDB may not support batch delete by ID in all versions

        # Rebuild docs for new + changed files
        all_sources: List[str] = []
        all_sources.extend(new_files.keys())
        all_sources.extend(changed_files.keys())

        rebuilt_docs: List[Document] = []
        for yml_path in all_sources:
            rebuilt_docs.extend(self._yaml_file_to_documents(Path(yml_path)))

        if rebuilt_docs:
            for doc in rebuilt_docs:
                doc.metadata = self._clean_metadata(doc.metadata)
            store.add_documents(rebuilt_docs)

        # Save updated hashes
        self._save_hashes(rebuilt_docs)

        try:
            collection = store._collection
            return collection.count()
        except Exception:
            return len(rebuilt_docs)

    # ── public: single-doc operations ───────────────────────────────

    def add_document(self, yaml_path: Path) -> int:
        """Index a single YAML file into the existing store."""
        store = self.load_existing()
        docs = self._yaml_file_to_documents(yaml_path)
        if not docs:
            return 0
        for doc in docs:
            doc.metadata = self._clean_metadata(doc.metadata)
        store.add_documents(docs)
        # Update hash records
        hashes = self._load_hashes()
        hashes[str(yaml_path)] = self._file_hash(yaml_path)
        stored = hashes.get("__doc_ids__", {})
        if isinstance(stored, dict):
            stored[str(yaml_path)] = [d.metadata.get("id", "") for d in docs]
            hashes["__doc_ids__"] = stored
        self._write_hashes(hashes)
        return len(docs)

    def remove_document(self, doc_id: str) -> bool:
        """Remove a document from the index by its metadata ID."""
        store = self.load_existing()
        try:
            # ChromaDB doesn't support delete by metadata filter directly,
            # but we can use the collection's get + delete flow
            results = store.get(where={"id": doc_id})
            if results and results["ids"]:
                store.delete(ids=results["ids"])
                return True
        except Exception:
            pass
        return False

    # ── ChromaDB instance (local or remote) ───────────────────────────

    def _create_chroma(self, collection_name: str | None = None) -> Chroma:
        """Create a ChromaDB client — HTTP remote or local embedded."""
        cn = collection_name or self._COLLECTION_NAME
        if self._http_url:
            from urllib.parse import urlparse
            import chromadb
            if self._http_client is None:
                parsed = urlparse(self._http_url)
                host = parsed.hostname or "localhost"
                port = parsed.port or 8000
                self._http_client = chromadb.HttpClient(host=host, port=port)
            return Chroma(
                client=self._http_client,
                collection_name=cn,
                embedding_function=self.embeddings,
            )
        else:
            return Chroma(
                persist_directory=str(self.persist_dir),
                embedding_function=self.embeddings,
                collection_name=cn,
            )

    def load_existing(self) -> Chroma:
        """Load an existing ChromaDB index (raises if not yet built)."""
        if self.embeddings is None:
            raise RuntimeError(
                getattr(self, "_unavailable_reason", "embedding 未配置")
            )
        return self._create_chroma()

    @staticmethod
    def _clean_metadata(meta: dict) -> dict:
        """Remove empty lists/strings from metadata (Chroma rejects them)."""
        return {k: v for k, v in meta.items() if v not in ([], "", None)}

    # ── file scanning ───────────────────────────────────────────────

    def _all_yaml_to_documents(self) -> List[Document]:
        """Convert all YAML files in kb_root to Documents."""
        docs: List[Document] = []
        docs += self._cards_to_documents()
        docs += self._papers_to_documents()
        docs += self._templates_to_documents()
        docs += self._problems_to_documents()
        for doc in docs:
            doc.metadata = self._clean_metadata(doc.metadata)
        return docs

    def _yaml_file_to_documents(self, yaml_path: Path) -> List[Document]:
        """Convert a single YAML file to its Document representation(s).

        Delegates to the loader to determine whether the file is a method
        card, paper, or template.
        """
        data = None
        try:
            import yaml
            data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        except Exception:
            return []

        if not data:
            return []

        if "method_card" in data:
            from .schemas import MethodCard
            card = MethodCard(**data["method_card"])
            return [self._card_to_document(card)]
        elif "paper" in data:
            from .schemas import Paper
            paper = Paper(**data["paper"])
            return [self._paper_to_document(paper)]
        elif "template" in data:
            from .schemas import Template
            tpl = Template(**data["template"])
            return [self._template_to_document(tpl)]
        elif "problem" in data:
            from .schemas import Problem
            prob = Problem(**data["problem"])
            return [self._problem_to_document(prob)]

        return []

    def _scan_all_files(self) -> Tuple[List[Document], Dict[str, Set[str]]]:
        """Scan all YAML files and return (documents, {filepath: {doc_ids}})."""
        docs = self._all_yaml_to_documents()
        file_to_ids: Dict[str, Set[str]] = {}

        # Map each document back to its source file
        for doc in docs:
            yml_path = doc.metadata.get("_source_file")
            if yml_path:
                file_to_ids.setdefault(yml_path, set()).add(doc.metadata.get("id", ""))

        return docs, file_to_ids

    # ── content → Document converters (with source tracking) ────────

    def _cards_to_documents(self) -> List[Document]:
        docs = []
        for card in self.loader.load_all_methods():
            doc = self._card_to_document(card)
            # Find source YAML path for this card
            source = self._find_source_file("methods", card.id)
            if source:
                doc.metadata["_source_file"] = str(source)
            docs.append(doc)
        return docs

    def _papers_to_documents(self) -> List[Document]:
        docs = []
        for paper in self.loader.load_all_papers():
            doc = self._paper_to_document(paper)
            source = self._find_source_file("papers", paper.id)
            if source:
                doc.metadata["_source_file"] = str(source)
            docs.append(doc)
        return docs

    def _templates_to_documents(self) -> List[Document]:
        docs = []
        for tpl in self.loader.load_all_templates():
            doc = self._template_to_document(tpl)
            source = self._find_source_file("templates", tpl.id)
            if source:
                doc.metadata["_source_file"] = str(source)
            docs.append(doc)
        return docs

    def _problems_to_documents(self) -> List[Document]:
        docs = []
        for prob in self.loader.load_all_problems():
            doc = self._problem_to_document(prob)
            source = self._find_source_file("problems", prob.id)
            if source:
                doc.metadata["_source_file"] = str(source)
            docs.append(doc)
        return docs

    def _find_source_file(self, subdir: str, doc_id: str) -> Optional[Path]:
        """Find the YAML file that produced a given document ID."""
        search_dir = self.kb_root / subdir
        if not search_dir.exists():
            return None
        for yf in search_dir.rglob("*.yaml"):
            try:
                import yaml
                data = yaml.safe_load(yf.read_text(encoding="utf-8"))
                if not data:
                    continue
                # Try all known top-level keys
                for key in ("method_card", "paper", "template", "problem"):
                    if key in data and isinstance(data[key], dict):
                        if data[key].get("id") == doc_id:
                            return yf
            except Exception:
                continue
        return None

    # Reuse the rich document builders from retriever for consistency
    @staticmethod
    def _card_to_document(card) -> Document:
        from .retriever import HybridRetriever
        return HybridRetriever._card_to_document(card)

    @staticmethod
    def _paper_to_document(paper) -> Document:
        from .retriever import HybridRetriever
        return HybridRetriever._paper_to_document(paper)

    @staticmethod
    def _template_to_document(tpl) -> Document:
        from .retriever import HybridRetriever
        return HybridRetriever._template_to_document(tpl)

    @staticmethod
    def _problem_to_document(prob) -> Document:
        from .retriever import HybridRetriever
        return HybridRetriever._problem_to_document(prob)

    # ── hash management ─────────────────────────────────────────────

    @staticmethod
    def _file_hash(path: Path) -> str:
        """SHA256 of a file's content."""
        if not path.exists():
            return ""
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def _load_hashes(self) -> dict:
        """Load the persisted hash metadata."""
        if not self._hash_path.exists():
            return {}
        try:
            return json.loads(self._hash_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_hashes(self, documents: List[Document]) -> None:
        """Compute and persist hashes for all documents currently in the index."""
        # Load existing to preserve records for unchanged files
        hashes = self._load_hashes()
        doc_map: Dict[str, List[str]] = {}  # path → [doc_id, ...]

        for doc in documents:
            src = doc.metadata.get("_source_file")
            if src:
                doc_map.setdefault(src, []).append(doc.metadata.get("id", ""))

        # Update hashes for each source file
        for yml_path, ids in doc_map.items():
            p = Path(yml_path)
            if p.exists():
                hashes[yml_path] = self._file_hash(p)
            if not isinstance(hashes.get("__doc_ids__"), dict):
                hashes["__doc_ids__"] = {}
            hashes["__doc_ids__"][yml_path] = ids

        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self._write_hashes(hashes)

    def _write_hashes(self, data: dict) -> None:
        """Write hash data to disk."""
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self._hash_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
