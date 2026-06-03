---
name: warn-python36-incompatible
enabled: true
event: file
pattern: from __future__ import annotations|tuple\[|dict\[|set\[|from agno import|from agno\.
---

⚠️ **Python 3.6 Compatibility Issue Detected!**

This code may not be compatible with Python 3.6.8:

**Patterns detected:**
- `from __future__ import annotations` - Not supported in Python 3.6
- `tuple[...]`, `dict[...]`, `set[...]` - Use `Tuple[...]`, `Dict[...]`, `Set[...]` instead

**Fix:**
```python
# ❌ Wrong
from __future__ import annotations
some_var: tuple[str, int] = ...

# ✅ Correct  
from typing import Tuple, Dict, Set
some_var: Tuple[str, int] = ...
```

Also: `from agno import` must be wrapped in try/except for optional import.