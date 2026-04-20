# Knowledge Context Auto-Injection

The CKS Knowledge Layer (`src/features/knowledge/`) provides automatic context injection:

- **AST-based chunking**: Python files are parsed by AST (not regex) for accurate function/class boundaries
- **Incremental indexing**: Files are tracked by timestamp, only re-indexed when modified
- **Auto-injection hook**: When you ask questions about implementing/debugging patterns, relevant code is automatically retrieved from CKS

## Usage

```python
from knowledge.chunking import PythonChunker
from knowledge.indexing import CKSIndexer
from knowledge.injection import before_message

# Chunk and index code
chunks = PythonChunker.chunk_file(Path("src/module.py"))
indexer = CKSIndexer()
stats = indexer.index_directory(Path("src/"), "**/*.py")

# Hook runs automatically via before_message.py
```

## When to Use

- "How do I implement X?" -> Searches CKS for similar patterns
- "Debug this error" -> Retrieves error handling patterns
- "Design a class for..." -> Finds class design examples
