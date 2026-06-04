"""
汉献帝之末路 v2.5.0 — 边缘 TTS 服务端模块
edge-tts 微软免费中文语音合成, 给前端 useTTS 备用
POST /api/tts { text, voice, rate, pitch } -> { audio: base64 mp3 }
v5.3.0 P7-3: 改为 lazy import (避免无 edge_tts 时整个模块加载失败)
"""
import asyncio
import base64
import logging
import tempfile
from pathlib import Path

log = logging.getLogger(__name__)

# v5.3.0 P7-3: lazy import 让 tts 模块本身可加载, 真正调 edge_tts 才 import
def _get_edge_tts():
    import edge_tts
    return edge_tts

# 中文语音 (男声威压 / 女声柔美)
ZH_VOICES = {
    'zh-CN-YunjianNeural': '云健 (男声威压, 圣旨首选)',
    'zh-CN-YunxiNeural': '云希 (男声温润, 奏折)',
    'zh-CN-YunyangNeural': '云扬 (男声新闻, 通用)',
    'zh-CN-XiaoxiaoNeural': '晓晓 (女声柔美, 大臣)',
    'zh-CN-YunxiaNeural': '云夏 (男声少年, 朝议)',
    'zh-CN-liaoning-XiaobeiNeural': '晓北 (东北口音, 趣味)',
}

DEFAULT_VOICE = 'zh-CN-YunjianNeural'


async def _synthesize(text: str, voice: str, rate: str, pitch: str) -> bytes:
    """异步合成语音 → MP3 bytes"""
    edge_tts = _get_edge_tts()
    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate,
        pitch=pitch,
    )
    buf = bytearray()
    async for chunk in communicate.stream():
        if chunk['type'] == 'audio':
            buf.extend(chunk['data'])
    return bytes(buf)


def text_to_audio_base64(text: str, voice: str = DEFAULT_VOICE,
                          rate: str = '-5%', pitch: str = '-10Hz') -> str:
    """
    同步包装: 文本 → base64 mp3
    用于 Flask 路由直接调用
    """
    if not text.strip():
        return ''
    try:
        audio_bytes = asyncio.run(_synthesize(text, voice, rate, pitch))
        return base64.b64encode(audio_bytes).decode('ascii')
    except Exception as e:
        log.error(f'edge-tts 合成失败: {e}')
        return ''


# CLI 调试: python -m han_sim.tts "汉献帝初平元年"
if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print(f'用法: python -m han_sim.tts "<text>" [voice]')
        print(f'可选 voice: {", ".join(ZH_VOICES.keys())}')
        sys.exit(1)
    text = sys.argv[1]
    voice = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_VOICE
    print(f'🎙️  合成: voice={voice} text={text[:40]}...')
    audio_b64 = text_to_audio_base64(text, voice)
    if audio_b64:
        # 写到临时文件播放
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            f.write(base64.b64decode(audio_b64))
            print(f'✅ 已生成: {f.name} ({len(audio_b64) // 1024} KB)')
    else:
        print('❌ 合成失败')
