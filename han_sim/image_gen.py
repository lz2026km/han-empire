"""v5.2.0 P6-10: MiniMax image-01 AI 生图 (curl 协议).

主公协议 (curl 形式):
  POST https://api.minimaxi.com/v1/image_generation
  Authorization: Bearer $MINIMAX_API_KEY
  Content-Type: application/json
  body: {"model":"image-01","prompt":"...","aspect_ratio":"16:9",
         "response_format":"url","n":3,"prompt_optimizer":true}

特性:
- 链式 fallback: MINIMAX_API_KEY (主) → 无 key 报错
- retry 1 + 60s 退避 (仿 ming_sim 5 RPM 限流经验)
- 支持 aspect_ratio: 1:1 / 16:9 / 9:16 / 4:3 / 3:4 / 1:2 / 2:1
- 支持 n: 1-4
- 自动下载 url → 本地文件

用法:
    from han_sim.image_gen import generate_image, download_image
    urls = generate_image("A Han dynasty palace", aspect_ratio="16:9", n=1)
    download_image(urls[0], "web/public/banner.jpg")
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import List, Optional

MINIMAX_URL = "https://api.minimaxi.com/v1/image_generation"
DEFAULT_MODEL = "image-01"
ALLOWED_ASPECT = {"1:1", "16:9", "9:16", "4:3", "3:4", "1:2", "2:1"}
DEFAULT_TIMEOUT = 90
RETRY_DELAY = 60  # 秒 (仿 ming_sim MiniMax 5 RPM 限流经验)
RETRY_MAX = 1


def _get_api_key() -> str:
    """v5.2.0 P6-10: 取 API key (env 优先, 启动时已 load .env)."""
    for k in ("MINIMAX_API_KEY", "OPENAI_API_KEY", "DEEPSEEK_API_KEY"):
        v = os.environ.get(k, "").strip()
        if v and v != "your_minimax_key_here":
            return v
    raise RuntimeError(
        "image_gen: 未找到 API key. 请设置 MINIMAX_API_KEY "
        "(或 OPENAI_API_KEY / DEEPSEEK_API_KEY) 环境变量 / .env 文件"
    )


def _build_payload(
    prompt: str,
    aspect_ratio: str = "16:9",
    n: int = 1,
    prompt_optimizer: bool = True,
    model: str = DEFAULT_MODEL,
) -> dict:
    if aspect_ratio not in ALLOWED_ASPECT:
        raise ValueError(
            f"image_gen: aspect_ratio {aspect_ratio!r} 不在 {ALLOWED_ASPECT} 中"
        )
    if not 1 <= n <= 4:
        raise ValueError("image_gen: n 必须在 1-4 之间")
    return {
        "model": model,
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "response_format": "url",
        "n": n,
        "prompt_optimizer": prompt_optimizer,
    }


def _post_minimax(payload: dict, api_key: str, timeout: int) -> dict:
    """v5.2.0 P6-10: 调 MiniMax image-01, 返 raw JSON dict. 失败抛 RuntimeError."""
    req = urllib.request.Request(
        MINIMAX_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"image_gen: HTTP {e.code} {e.reason} - {body[:300]}"
        ) from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"image_gen: URL 错误 - {e}") from e
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"image_gen: 响应非 JSON - {raw[:300]}") from e


def _extract_urls(payload: dict) -> List[str]:
    """v5.2.0 P6-10: 解析 MiniMax 响应, 返 url 列表. 兼容 2 种格式."""
    # 格式 A: data.image_urls[0..n-1]
    data = payload.get("data") or {}
    if isinstance(data, dict):
        urls = data.get("image_urls")
        if isinstance(urls, list) and urls:
            return [str(u) for u in urls]
    # 格式 B: images[].url
    images = payload.get("images")
    if isinstance(images, list) and images:
        out = []
        for it in images:
            if isinstance(it, dict) and it.get("url"):
                out.append(str(it["url"]))
        if out:
            return out
    # 格式 C: 单 url
    if data.get("url"):
        return [str(data["url"])]
    raise RuntimeError(f"image_gen: 响应中无 url - {json.dumps(payload)[:300]}")


def generate_image(
    prompt: str,
    aspect_ratio: str = "16:9",
    n: int = 1,
    prompt_optimizer: bool = True,
    model: str = DEFAULT_MODEL,
    timeout: int = DEFAULT_TIMEOUT,
) -> List[str]:
    """v5.2.0 P6-10: 生图, 返 url 列表 (n 张)."""
    api_key = _get_api_key()
    payload = _build_payload(prompt, aspect_ratio, n, prompt_optimizer, model)
    last_err: Optional[Exception] = None
    for attempt in range(RETRY_MAX + 1):
        try:
            resp = _post_minimax(payload, api_key, timeout)
            return _extract_urls(resp)
        except RuntimeError as e:
            last_err = e
            if attempt < RETRY_MAX:
                time.sleep(RETRY_DELAY)
                continue
            break
    raise RuntimeError(
        f"image_gen: 重试 {RETRY_MAX} 次仍失败: {last_err}"
    )


def download_image(url: str, save_path: str, timeout: int = 60) -> bool:
    """v5.2.0 P6-10: 下载 url 到本地. 成功返 True."""
    os.makedirs(os.path.dirname(os.path.abspath(save_path)) or ".", exist_ok=True)
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            data = resp.read()
        with open(save_path, "wb") as f:
            f.write(data)
        return True
    except Exception as e:
        raise RuntimeError(f"image_gen: 下载失败 {url} → {save_path}: {e}") from e
