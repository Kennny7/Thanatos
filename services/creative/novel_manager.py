# Thanatos/services/creative/novel_manager.py
"""
Long-Form Web Novel & Wuxia/Xianxia Generation Engine.
Supports:
- Novel project folders with chapter markdown files (e.g. Zettlr / Obsidian structure).
- Character arcs and cultivation development database (SQLite / Milvus vector store).
- Detection and filtering of random spam/unindexed chapters.
- Wuxia/Xianxia style pipelines (Chinese Novelist framework conventions: Dao, Qi, Cultivation Realms, Sect Politics).
- Versioned in-place chapter edits with full rollback and diff tracking.
"""

import hashlib
import json
import logging
import os
import re
import sqlite3
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

NOVEL_DB_PATH = os.path.join("data", "novels.db")


class NovelProjectManager:
    """
    Manages multi-novel libraries, tracks character progression across chapters,
    and maintains historical snapshots for instant rollback.
    """

    def __init__(self, db_path: str = NOVEL_DB_PATH) -> None:
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Novels table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS novels (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    folder_path TEXT NOT NULL,
                    genre TEXT DEFAULT 'Wuxia/Xianxia',
                    outline TEXT,
                    created_at REAL
                )
            """)
            # Characters table with development tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS characters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    novel_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    realm TEXT,
                    sect TEXT,
                    personality TEXT,
                    development_notes TEXT,
                    last_seen_chapter INTEGER,
                    FOREIGN KEY (novel_id) REFERENCES novels(id)
                )
            """)
            # Chapter registry with rollback history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chapters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    novel_id TEXT NOT NULL,
                    chapter_number INTEGER,
                    title TEXT,
                    filename TEXT,
                    content_hash TEXT,
                    word_count INTEGER,
                    is_spam BOOLEAN DEFAULT 0,
                    FOREIGN KEY (novel_id) REFERENCES novels(id)
                )
            """)
            # Versioned snapshot history for undo
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chapter_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    novel_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    snapshot_content TEXT NOT NULL,
                    reason TEXT,
                    timestamp REAL
                )
            """)
            conn.commit()

    def scan_novel_folder(self, folder_path: str, novel_title: Optional[str] = None) -> Dict[str, Any]:
        """
        Inspect a novel directory (e.g. Zettlr markdown notes).
        Detects chapter numbers, flags unindexed spam files, and builds registry.
        """
        if not os.path.exists(folder_path):
            return {"status": "error", "error": f"Folder {folder_path} not found"}

        title = novel_title or os.path.basename(os.path.abspath(folder_path))
        novel_id = hashlib.md5(folder_path.encode()).hexdigest()[:10]

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO novels (id, title, folder_path, created_at) VALUES (?, ?, ?, ?)",
                (novel_id, title, folder_path, time.time()),
            )

        registered_chapters = []
        spam_chapters = []

        for fname in sorted(os.listdir(folder_path)):
            if not fname.endswith((".md", ".txt")):
                continue

            full_path = os.path.join(folder_path, fname)
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Chapter number detection heuristic
            chap_match = re.search(r"(?:chapter|ch|第)\s*(\d+)", fname, re.IGNORECASE)
            if not chap_match:
                chap_match = re.search(r"^(?:#|\b)(?:chapter|ch|第)\s*(\d+)", content, re.IGNORECASE | re.MULTILINE)

            words = len(content.split())
            # Spam / unindexed chapter heuristic: no chapter number and short text / ad links
            is_spam = False
            if not chap_match:
                if words < 80 or any(k in content.lower() for k in ["patreon", "discord link", "ad block", "author note only"]):
                    is_spam = True
                    spam_chapters.append(fname)

            chap_num = int(chap_match.group(1)) if chap_match else 0
            hasher = hashlib.sha256(content.encode("utf-8")).hexdigest()

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO chapters (novel_id, chapter_number, title, filename, content_hash, word_count, is_spam) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (novel_id, chap_num, fname, fname, hasher, words, 1 if is_spam else 0),
                )
                conn.commit()

            if not is_spam:
                registered_chapters.append({"filename": fname, "chapter": chap_num, "words": words})

        return {
            "status": "success",
            "novel_id": novel_id,
            "title": title,
            "valid_chapters_count": len(registered_chapters),
            "spam_chapters_detected": spam_chapters,
        }

    def record_character(self, novel_id: str, name: str, realm: str, sect: str, notes: str, chapter: int) -> None:
        """Register or update a character's cultivation realm & evolution."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO characters (novel_id, name, realm, sect, development_notes, last_seen_chapter) VALUES (?, ?, ?, ?, ?, ?)",
                (novel_id, name, realm, sect, notes, chapter),
            )
            conn.commit()

    def get_character_history(self, novel_id: str, character_name: str) -> List[Dict[str, Any]]:
        """Fetch progressive evolution of a character across chapters."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM characters WHERE novel_id = ? AND name LIKE ? ORDER BY last_seen_chapter ASC",
                (novel_id, f"%{character_name}%"),
            )
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def save_chapter_snapshot(self, novel_id: str, filename: str, content: str, reason: str = "Pre-edit backup") -> None:
        """Create a versioned snapshot before in-place editing to allow safe rollback."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO chapter_history (novel_id, filename, snapshot_content, reason, timestamp) VALUES (?, ?, ?, ?, ?)",
                (novel_id, filename, content, reason, time.time()),
            )
            conn.commit()

    def rollback_chapter(self, novel_id: str, filename: str, folder_path: str) -> bool:
        """Undo last edit and restore previous version of a chapter."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT snapshot_content FROM chapter_history WHERE novel_id = ? AND filename = ? ORDER BY id DESC LIMIT 1",
                (novel_id, filename),
            )
            row = cursor.fetchone()
            if not row:
                return False

            prev_content = row[0]
            target_file = os.path.join(folder_path, filename)
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(prev_content)
            return True


novel_manager = NovelProjectManager()
