# Thanatos/services/agents/trait_engine.py
"""
Reinforcement Learning Trait Engine — The Heart of Agent Evolution.

Manages the continuous numerical personality trait vectors for all agents.
Traits are stored in PostgreSQL (with SQLite fallback) and evolve through
a contextual bandit RL loop:

    State (traits) → LLM Prompt → Response → Feedback → Trait Update

Learning Formula:
    new_trait = clamp(old_trait + (learning_rate × reward × direction), floor, ceiling)

Where:
    - learning_rate: 0.03 (conservative, ~33 interactions to shift 1.0)
    - reward: [-1.0, +1.0] signal from feedback engine
    - direction: trait's deviation from neutral (0.5), biased toward reinforcement
    - floor/ceiling: persona-specific hard boundaries from agent_personas.py
"""

import json
import logging
import os
import sqlite3
import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

from services.agents.agent_personas import (
    ALL_PERSONAS,
    TRAIT_DIMENSIONS,
    PersonaBlueprint,
    get_persona,
)

# RL Hyperparameters
DEFAULT_LEARNING_RATE = 0.03
TRAIT_GLOBAL_FLOOR = 0.05
TRAIT_GLOBAL_CEILING = 0.95
DECAY_RATE = 0.001  # Slow drift back toward baseline per interaction (homeostasis)

TRAIT_DB_DIR = os.path.join("data", "trait_engine")
TRAIT_SQLITE_PATH = os.path.join(TRAIT_DB_DIR, "traits.db")
EVOLUTION_LOG_PATH = os.path.join(TRAIT_DB_DIR, "evolution_log.jsonl")


class TraitEngine:
    """
    Core RL engine for agent personality evolution.

    Reads/writes trait vectors to PostgreSQL when available,
    falls back to local SQLite. Logs all mutations to both
    MongoDB (via enterprise_db) and a local JSONL file.
    """

    def __init__(self, learning_rate: float = DEFAULT_LEARNING_RATE) -> None:
        self.learning_rate = learning_rate
        self._pg_conn = None
        self._is_pg_online = False
        os.makedirs(TRAIT_DB_DIR, exist_ok=True)
        self._init_sqlite()
        self._try_connect_postgres()
        self._seed_baselines()

    # ------------------------------------------------------------------
    # Database Initialization
    # ------------------------------------------------------------------

    def _init_sqlite(self) -> None:
        """Create local SQLite tables for trait storage and evolution logging."""
        with sqlite3.connect(TRAIT_SQLITE_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_traits (
                    agent_id TEXT PRIMARY KEY,
                    traits_json TEXT NOT NULL,
                    updated_at REAL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trait_evolution_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT,
                    trait_name TEXT,
                    old_value REAL,
                    new_value REAL,
                    reward REAL,
                    trigger_type TEXT,
                    trigger_detail TEXT,
                    timestamp REAL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_topic_affinities (
                    agent_id TEXT,
                    topic TEXT,
                    affinity REAL DEFAULT 0.5,
                    PRIMARY KEY (agent_id, topic)
                )
            """)
            conn.commit()

    def _try_connect_postgres(self) -> bool:
        """Attempt connection to enterprise PostgreSQL for trait persistence."""
        try:
            import psycopg2
            from services.database.enterprise_database_service import PG_HOST, PG_PORT, PG_USER, PG_PASSWORD, PG_DB
            conn = psycopg2.connect(
                host=PG_HOST, port=PG_PORT, user=PG_USER,
                password=PG_PASSWORD, dbname=PG_DB, connect_timeout=2,
            )
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS agent_traits (
                        agent_id VARCHAR(64) PRIMARY KEY,
                        traits_json TEXT NOT NULL,
                        updated_at DOUBLE PRECISION
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS trait_evolution_log (
                        id SERIAL PRIMARY KEY,
                        agent_id VARCHAR(64),
                        trait_name VARCHAR(64),
                        old_value DOUBLE PRECISION,
                        new_value DOUBLE PRECISION,
                        reward DOUBLE PRECISION,
                        trigger_type VARCHAR(32),
                        trigger_detail TEXT,
                        timestamp DOUBLE PRECISION
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS agent_topic_affinities (
                        agent_id VARCHAR(64),
                        topic VARCHAR(128),
                        affinity DOUBLE PRECISION DEFAULT 0.5,
                        PRIMARY KEY (agent_id, topic)
                    );
                """)
            self._pg_conn = conn
            self._is_pg_online = True
            logger.info("TraitEngine connected to PostgreSQL for trait persistence.")
            return True
        except Exception as e:
            logger.debug("TraitEngine PostgreSQL unavailable, using SQLite fallback: %s", e)
            self._is_pg_online = False
            return False

    def _is_online(self) -> bool:
        if not self._is_pg_online:
            return self._try_connect_postgres()
        try:
            with self._pg_conn.cursor() as cur:
                cur.execute("SELECT 1;")
            return True
        except Exception:
            self._is_pg_online = False
            return False

    # ------------------------------------------------------------------
    # Baseline Seeding
    # ------------------------------------------------------------------

    def _seed_baselines(self) -> None:
        """Write baseline trait vectors for any agents not yet in the database."""
        for agent_id, persona in ALL_PERSONAS.items():
            existing = self._read_traits_raw(agent_id)
            if existing is None:
                self._write_traits_raw(agent_id, persona.baseline_traits)
                self._seed_topic_affinities(agent_id, persona)
                logger.info("Seeded baseline traits for agent '%s'", agent_id)

    def _seed_topic_affinities(self, agent_id: str, persona: PersonaBlueprint) -> None:
        """Initialize topic affinity scores from persona seed keywords."""
        now = time.time()
        for topic in persona.topic_seeds:
            affinity = 0.8  # High initial affinity for seed topics
            if self._is_online():
                try:
                    with self._pg_conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO agent_topic_affinities (agent_id, topic, affinity)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (agent_id, topic) DO NOTHING
                        """, (agent_id, topic, affinity))
                    continue
                except Exception:
                    self._is_pg_online = False

            with sqlite3.connect(TRAIT_SQLITE_PATH) as conn:
                conn.execute(
                    "INSERT OR IGNORE INTO agent_topic_affinities (agent_id, topic, affinity) VALUES (?, ?, ?)",
                    (agent_id, topic, affinity),
                )

    # ------------------------------------------------------------------
    # Trait Read/Write
    # ------------------------------------------------------------------

    def _read_traits_raw(self, agent_id: str) -> Optional[Dict[str, float]]:
        """Read raw trait JSON from database."""
        if self._is_online():
            try:
                with self._pg_conn.cursor() as cur:
                    cur.execute("SELECT traits_json FROM agent_traits WHERE agent_id = %s", (agent_id,))
                    row = cur.fetchone()
                    if row:
                        return json.loads(row[0])
                    return None
            except Exception:
                self._is_pg_online = False

        with sqlite3.connect(TRAIT_SQLITE_PATH) as conn:
            row = conn.execute(
                "SELECT traits_json FROM agent_traits WHERE agent_id = ?", (agent_id,)
            ).fetchone()
            if row:
                return json.loads(row[0])
        return None

    def _write_traits_raw(self, agent_id: str, traits: Dict[str, float]) -> None:
        """Persist trait vector to database."""
        traits_json = json.dumps(traits)
        now = time.time()

        if self._is_online():
            try:
                with self._pg_conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO agent_traits (agent_id, traits_json, updated_at)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (agent_id) DO UPDATE
                        SET traits_json = EXCLUDED.traits_json, updated_at = EXCLUDED.updated_at
                    """, (agent_id, traits_json, now))
                return
            except Exception:
                self._is_pg_online = False

        with sqlite3.connect(TRAIT_SQLITE_PATH) as conn:
            conn.execute(
                "INSERT INTO agent_traits (agent_id, traits_json, updated_at) VALUES (?, ?, ?) "
                "ON CONFLICT(agent_id) DO UPDATE SET traits_json = excluded.traits_json, updated_at = excluded.updated_at",
                (agent_id, traits_json, now),
            )

    def get_traits(self, agent_id: str) -> Dict[str, float]:
        """
        Get the LIVE trait vector for an agent.
        Returns the evolved values, not the baseline.
        Falls back to baseline if not yet persisted.
        """
        traits = self._read_traits_raw(agent_id)
        if traits is not None:
            return traits

        # Try legacy ID mapping
        from services.agents.agent_personas import LEGACY_ID_MAP
        resolved = LEGACY_ID_MAP.get(agent_id, agent_id)
        if resolved != agent_id:
            traits = self._read_traits_raw(resolved)
            if traits is not None:
                return traits

        # Fall back to baseline
        try:
            persona = get_persona(agent_id)
            return dict(persona.baseline_traits)
        except KeyError:
            # Unknown agent, return neutral vector
            return {dim: 0.5 for dim in TRAIT_DIMENSIONS}

    def get_topic_affinities(self, agent_id: str) -> Dict[str, float]:
        """Get all topic affinity scores for an agent."""
        affinities: Dict[str, float] = {}

        if self._is_online():
            try:
                with self._pg_conn.cursor() as cur:
                    cur.execute(
                        "SELECT topic, affinity FROM agent_topic_affinities WHERE agent_id = %s",
                        (agent_id,)
                    )
                    for topic, aff in cur.fetchall():
                        affinities[topic] = aff
                return affinities
            except Exception:
                self._is_pg_online = False

        with sqlite3.connect(TRAIT_SQLITE_PATH) as conn:
            for topic, aff in conn.execute(
                "SELECT topic, affinity FROM agent_topic_affinities WHERE agent_id = ?",
                (agent_id,)
            ).fetchall():
                affinities[topic] = aff
        return affinities

    # ------------------------------------------------------------------
    # RL Core: Reward Application
    # ------------------------------------------------------------------

    def apply_reward(
        self,
        agent_id: str,
        reward: float,
        trigger_type: str = "explicit",
        trigger_detail: str = "",
        active_trait_weights: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Apply a reward signal to an agent's trait vector.

        Args:
            agent_id: Which agent to update.
            reward: Signal in [-1.0, +1.0]. Positive reinforces, negative dampens.
            trigger_type: 'explicit' (user rated), 'implicit' (sentiment), 'inter_agent'.
            trigger_detail: Description of what triggered the reward.
            active_trait_weights: Optional per-trait influence weights for this interaction.
                                 If None, all traits are updated equally based on their deviation.

        Returns:
            Dict with old traits, new traits, and changes made.
        """
        reward = max(-1.0, min(1.0, reward))
        current_traits = self.get_traits(agent_id)
        new_traits = dict(current_traits)
        changes: List[Dict[str, Any]] = []

        try:
            persona = get_persona(agent_id)
            floors = persona.trait_floors
            ceilings = persona.trait_ceilings
            baseline = persona.baseline_traits
        except KeyError:
            floors, ceilings, baseline = {}, {}, {}

        for trait_name in TRAIT_DIMENSIONS:
            old_val = current_traits.get(trait_name, 0.5)
            base_val = baseline.get(trait_name, 0.5)

            # Compute direction: how far the trait deviates from neutral (0.5)
            # Positive reward pushes trait further in its current direction
            # Negative reward pulls trait back toward baseline
            deviation = old_val - 0.5
            if reward >= 0:
                direction = 1.0 if deviation >= 0 else -1.0
                direction *= abs(deviation) + 0.1  # Scale by how far we've deviated
            else:
                # Negative reward: drift toward baseline
                direction = (base_val - old_val)
                direction = 1.0 if direction >= 0 else -1.0

            # Apply per-trait weight if provided
            weight = 1.0
            if active_trait_weights and trait_name in active_trait_weights:
                weight = active_trait_weights[trait_name]

            # Compute delta
            delta = self.learning_rate * reward * direction * weight

            # Apply homeostasis decay (gentle drift toward baseline)
            decay = DECAY_RATE * (base_val - old_val)
            delta += decay

            # Compute new value with clamping
            floor = max(TRAIT_GLOBAL_FLOOR, floors.get(trait_name, TRAIT_GLOBAL_FLOOR))
            ceiling = min(TRAIT_GLOBAL_CEILING, ceilings.get(trait_name, TRAIT_GLOBAL_CEILING))
            new_val = max(floor, min(ceiling, old_val + delta))

            if abs(new_val - old_val) > 0.001:
                new_traits[trait_name] = round(new_val, 4)
                changes.append({
                    "trait": trait_name,
                    "old": round(old_val, 4),
                    "new": round(new_val, 4),
                    "delta": round(new_val - old_val, 4),
                })

        # Persist updated traits
        self._write_traits_raw(agent_id, new_traits)

        # Log evolution
        self._log_evolution(agent_id, changes, reward, trigger_type, trigger_detail)

        result = {
            "agent_id": agent_id,
            "reward": reward,
            "trigger_type": trigger_type,
            "changes_count": len(changes),
            "changes": changes,
        }
        if changes:
            logger.info(
                "TraitEngine: Applied reward %.2f to '%s' (%s) — %d traits shifted.",
                reward, agent_id, trigger_type, len(changes),
            )
        return result

    def _log_evolution(
        self,
        agent_id: str,
        changes: List[Dict[str, Any]],
        reward: float,
        trigger_type: str,
        trigger_detail: str,
    ) -> None:
        """Log trait changes to database and local JSONL."""
        now = time.time()

        # JSONL log (always written, even if DB is down)
        for change in changes:
            log_entry = {
                "agent_id": agent_id,
                "trait": change["trait"],
                "old": change["old"],
                "new": change["new"],
                "reward": reward,
                "trigger_type": trigger_type,
                "trigger_detail": trigger_detail[:200],
                "timestamp": now,
            }
            try:
                with open(EVOLUTION_LOG_PATH, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry) + "\n")
            except Exception:
                pass

        # Database log
        for change in changes:
            if self._is_online():
                try:
                    with self._pg_conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO trait_evolution_log
                                (agent_id, trait_name, old_value, new_value, reward, trigger_type, trigger_detail, timestamp)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            agent_id, change["trait"], change["old"], change["new"],
                            reward, trigger_type, trigger_detail[:200], now,
                        ))
                    continue
                except Exception:
                    self._is_pg_online = False

            with sqlite3.connect(TRAIT_SQLITE_PATH) as conn:
                conn.execute(
                    "INSERT INTO trait_evolution_log "
                    "(agent_id, trait_name, old_value, new_value, reward, trigger_type, trigger_detail, timestamp) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (agent_id, change["trait"], change["old"], change["new"],
                     reward, trigger_type, trigger_detail[:200], now),
                )

    # ------------------------------------------------------------------
    # Topic Affinity Evolution
    # ------------------------------------------------------------------

    def update_topic_affinity(self, agent_id: str, topic: str, delta: float) -> None:
        """Adjust an agent's affinity for a topic based on interaction patterns."""
        affinities = self.get_topic_affinities(agent_id)
        old_val = affinities.get(topic, 0.3)
        new_val = max(0.05, min(0.95, old_val + delta))

        if self._is_online():
            try:
                with self._pg_conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO agent_topic_affinities (agent_id, topic, affinity)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (agent_id, topic) DO UPDATE
                        SET affinity = EXCLUDED.affinity
                    """, (agent_id, topic, new_val))
                return
            except Exception:
                self._is_pg_online = False

        with sqlite3.connect(TRAIT_SQLITE_PATH) as conn:
            conn.execute(
                "INSERT INTO agent_topic_affinities (agent_id, topic, affinity) VALUES (?, ?, ?) "
                "ON CONFLICT(agent_id, topic) DO UPDATE SET affinity = excluded.affinity",
                (agent_id, topic, new_val),
            )

    # ------------------------------------------------------------------
    # Introspection / Diagnostics
    # ------------------------------------------------------------------

    def get_trait_history(self, agent_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent trait evolution events for an agent."""
        history: List[Dict[str, Any]] = []

        if self._is_online():
            try:
                with self._pg_conn.cursor() as cur:
                    cur.execute("""
                        SELECT trait_name, old_value, new_value, reward, trigger_type, trigger_detail, timestamp
                        FROM trait_evolution_log
                        WHERE agent_id = %s
                        ORDER BY timestamp DESC
                        LIMIT %s
                    """, (agent_id, limit))
                    for row in cur.fetchall():
                        history.append({
                            "trait": row[0], "old": row[1], "new": row[2],
                            "reward": row[3], "trigger": row[4], "detail": row[5],
                            "timestamp": row[6],
                        })
                return history
            except Exception:
                self._is_pg_online = False

        with sqlite3.connect(TRAIT_SQLITE_PATH) as conn:
            for row in conn.execute(
                "SELECT trait_name, old_value, new_value, reward, trigger_type, trigger_detail, timestamp "
                "FROM trait_evolution_log WHERE agent_id = ? ORDER BY timestamp DESC LIMIT ?",
                (agent_id, limit),
            ).fetchall():
                history.append({
                    "trait": row[0], "old": row[1], "new": row[2],
                    "reward": row[3], "trigger": row[4], "detail": row[5],
                    "timestamp": row[6],
                })
        return history

    def get_all_agent_snapshots(self) -> Dict[str, Dict[str, float]]:
        """Get current trait vectors for all registered agents."""
        return {aid: self.get_traits(aid) for aid in ALL_PERSONAS}

    def reset_to_baseline(self, agent_id: str) -> Dict[str, Any]:
        """Hard reset an agent's traits back to their persona baseline."""
        try:
            persona = get_persona(agent_id)
        except KeyError:
            return {"success": False, "error": f"Unknown agent: {agent_id}"}

        old_traits = self.get_traits(agent_id)
        self._write_traits_raw(agent_id, persona.baseline_traits)
        self._log_evolution(
            agent_id,
            [{"trait": k, "old": old_traits.get(k, 0.5), "new": v, "delta": v - old_traits.get(k, 0.5)}
             for k, v in persona.baseline_traits.items()],
            0.0, "manual_reset", "User-initiated baseline reset",
        )
        return {
            "success": True,
            "agent_id": agent_id,
            "message": f"Reset {persona.name} to baseline traits.",
        }


# Global singleton
trait_engine = TraitEngine()
