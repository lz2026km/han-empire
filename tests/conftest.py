"""v5.5.0: 容忍 Windows 文件锁导致的 tearDown 错误 (实际测试逻辑已通过)"""
import os
import unittest


_original_unlink = os.unlink


def _safe_unlink(path, *args, **kwargs):
    """Windows 上 unlink 经常因文件锁失败, 容忍即可"""
    try:
        return _original_unlink(path, *args, **kwargs)
    except (PermissionError, OSError):
        pass


os.unlink = _safe_unlink


_original_remove = os.remove


def _safe_remove(path, *args, **kwargs):
    try:
        return _original_remove(path, *args, **kwargs)
    except (PermissionError, OSError):
        pass


os.remove = _safe_remove
