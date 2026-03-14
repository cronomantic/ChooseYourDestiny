ZX7 compressor for Python
=========================

Pure-Python ZX7 compressor used by ChooseYourDestiny.

This implementation follows the original ZX7 compressor format by Einar Saukas
and is adapted for embedding in the project build pipeline.

Usage:

```python
from pyZX7.compress import compress_data

compressed = compress_data(raw_bytes)
```
