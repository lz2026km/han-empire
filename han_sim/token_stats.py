"""LLM Token 统计与流式推理日志。"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict
import threading

@dataclass
class TokenStats:
    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0
    model: str = ""
    duration_ms: int = 0
    timestamp: str = ""
    role: str = ""  # simulator/extractor/decree_writer/memory_retrieval/...

class TokenStatsCollector:
    """全局 Token 统计收集器（单例）"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._stats: List[TokenStats] = []
            cls._instance._lock = threading.Lock()
        return cls._instance

    def record(self, stats: TokenStats):
        with self._lock:
            self._stats.append(stats)

    def get_stats(self, role: Optional[str] = None) -> List[TokenStats]:
        with self._lock:
            if role:
                return [s for s in self._stats if s.role == role]
            return list(self._stats)

    def summary(self) -> dict:
        with self._lock:
            if not self._stats:
                return {"total_calls": 0, "total_tokens": 0, "total_cost": 0.0}
            return {
                "total_calls": len(self._stats),
                "total_tokens": sum(s.total_tokens for s in self._stats),
                "total_cost": sum(s.cost for s in self._stats),
                "by_role": {
                    role: {"calls": len([s for s in self._stats if s.role == role]),
                           "tokens": sum(s.total_tokens for s in self._stats if s.role == role)}
                    for role in set(s.role for s in self._stats)
                }
            }

    def clear(self):
        with self._lock:
            self._stats.clear()

def record_stream_metrics(role: str, model: str, input_tokens: int,
                          output_tokens: int, reasoning_tokens: int,
                          duration_ms: int, cost: float = 0.0) -> TokenStats:
    """记录单次 LLM 调用"""
    collector = TokenStatsCollector()
    stats = TokenStats(
        input_tokens=input_tokens, output_tokens=output_tokens,
        reasoning_tokens=reasoning_tokens,
        total_tokens=input_tokens + output_tokens + reasoning_tokens,
        cost=cost, model=model, duration_ms=duration_ms,
        timestamp=datetime.now().isoformat(), role=role,
    )
    collector.record(stats)
    return stats

def get_token_summary() -> dict:
    return TokenStatsCollector().summary()
