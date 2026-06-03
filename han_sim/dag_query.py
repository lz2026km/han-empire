"""
dag_query.py — DAG 性能查询 (v3.2)
节点剪枝 / 分层加载 / LOD
"""
from __future__ import annotations
from typing import Dict, List, Any, Optional


class DAGQuery:
    """DAG 性能查询优化"""

    @staticmethod
    def prune_by_status(nodes: List[Dict], view_box: Optional[Dict] = None,
                       visible_only: bool = False) -> List[Dict]:
        """按状态剪枝节点"""
        if not visible_only:
            return nodes
        # 只返回未锁定节点 (减少可见节点数)
        return [n for n in nodes if n.get("status") != "locked"]

    @staticmethod
    def lod_simplify(nodes: List[Dict], threshold: int = 100) -> List[Dict]:
        """层级细节 (LOD): 节点 > threshold 用简笔"""
        if len(nodes) <= threshold:
            return nodes
        # 简笔: 移除 description / effects 细节
        return [
            {k: v for k, v in n.items() if k in ("id", "name", "line", "tier", "status", "cost")}
            for n in nodes
        ]

    @staticmethod
    def get_viewport_nodes(nodes: List[Dict], viewport: Dict, margin: int = 100) -> List[Dict]:
        """只返回视口内节点 (含 margin)"""
        vx, vy = viewport.get("x", 0), viewport.get("y", 0)
        vw, vh = viewport.get("w", 1920), viewport.get("h", 1080)
        visible = []
        for n in nodes:
            nx, ny = n.get("x", 0), n.get("y", 0)
            if (vx - margin <= nx <= vx + vw + margin and
                vy - margin <= ny <= vy + vh + margin):
                visible.append(n)
        return visible

    @staticmethod
    def batch_by_tier(nodes: List[Dict]) -> List[List[Dict]]:
        """按 tier 批量加载"""
        tiers: Dict[int, List[Dict]] = {}
        for n in nodes:
            t = n.get("tier", 0)
            tiers.setdefault(t, []).append(n)
        return [tiers[k] for k in sorted(tiers.keys())]

    @staticmethod
    def get_stats(nodes: List[Dict]) -> Dict[str, Any]:
        """统计"""
        return {
            "total": len(nodes),
            "by_status": {
                "unlocked": sum(1 for n in nodes if n.get("status") == "unlocked"),
                "available": sum(1 for n in nodes if n.get("status") == "available"),
                "locked": sum(1 for n in nodes if n.get("status") == "locked"),
            },
            "by_line": {
                line: sum(1 for n in nodes if n.get("line") == line)
                for line in set(n.get("line") for n in nodes)
            },
            "lod_simplified": len(nodes) > 100,
        }


_q: Optional[DAGQuery] = None


def get_dag_query() -> DAGQuery:
    global _q
    if _q is None:
        _q = DAGQuery()
    return _q
