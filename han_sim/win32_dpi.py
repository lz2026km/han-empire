# Windows DPI Awareness Module
import ctypes
import sys

def setup_dpi_awareness():
    """Configure Windows DPI awareness for sharp UI rendering."""
    if sys.platform != 'win32':
        return
    
    try:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except (OSError, AttributeError):
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except (OSError, AttributeError):
                pass
    except Exception:
        pass

def get_dpi_scale():
    """Get current DPI scaling factor."""
    if sys.platform != 'win32':
        return 1.0
    try:
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        dc = user32.GetDC(0)
        gdi32 = ctypes.windll.gdi32
        dpi = gdi32.GetDeviceCaps(dc, 88)
        user32.ReleaseDC(0, dc)
        return dpi / 96.0
    except Exception:
        return 1.0