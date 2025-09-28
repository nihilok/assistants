import pytest
import re
from assistants.cli.utils import highlight_code_blocks

SIMPLE_MD = """
# Title

Some text before code.

```python
def foo():
    return 'bar'
```

Some text after code.
"""

def strip_ansi(text):
    ansi_escape = re.compile(r'\x1b\[[0-9;]*[mK]')
    return ansi_escape.sub('', text)

def test_highlight_code_block_basic():
    result = highlight_code_blocks(SIMPLE_MD)
    plain = strip_ansi(result)
    assert "def foo():" in plain
    assert "return 'bar'" in plain
    assert "# Title" in plain
    assert "Some text before code." in plain
    assert "Some text after code." in plain

def test_highlight_code_block_no_code():
    md = "This is just text. No code blocks."
    result = highlight_code_blocks(md)
    plain = strip_ansi(result)
    assert "This is just text." in plain

def test_highlight_code_block_multiple():
    md = """
Text before.
```python
print('hi')
```
Middle text.
```js
console.log('hi')
```
Text after.
"""
    result = highlight_code_blocks(md)
    plain = strip_ansi(result)
    assert "print('hi')" in plain
    assert "console.log('hi')" in plain
    assert "Text before." in plain
    assert "Middle text." in plain
    assert "Text after." in plain
