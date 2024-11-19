# Talkie

A Python package for conversational AI interactions, enabling seamless chat-based interactions with AI models and RAG (Retrieval-Augmented Generation) capabilities.

## Features

- Quick chat interactions with AI models
- Support for RAG (Retrieval-Augmented Generation) with directory-based context
- Flexible conversation management and storage
- CLI interface for easy interactions
- Configurable AI model settings and API endpoints
- File-based chat history management

## Installation

This project uses Poetry for dependency management. To install:

```bash
# Clone the repository
git clone https://github.com/yourusername/talkie.git
cd talkie

# Install with Poetry
poetry install
```

## Requirements

- Python 3.12 or higher
- OpenAI API key

## Configuration

1. Create a `.env` file in the project root:
```
OPENAI_API_KEY=your_api_key_here
```

2. The package uses default configurations that can be customized through the CLI or programmatic interface.

## Usage

### Quick Chat

```python
from talkie.chat.quick import quick_chat

# Simple question
response = await quick_chat("What is the capital of France?")

# With RAG context from a directory
response = await quick_chat(
    question="What are the key points in the documentation?",
    rag_directory="./docs"
)
```

### CLI Commands

```bash
# Quick chat
talkie quick "What is the weather like today?"

# Create a new chat file
talkie create "my_chat" --dir "./context_directory"

# Ask a question in an existing chat
talkie ask "./chats/my_chat.md"
```

## Development

For development work:

```bash
# Install dev dependencies
poetry install --with dev

# Run tests
pytest

# Format code
black .
```

## Project Structure

- `chat/`: Core chat functionality and AI interactions
- `cli/`: Command-line interface implementations
- `fsutils/`: File system utilities
- `rag/`: Retrieval-Augmented Generation functionality

## License

MIT License

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
