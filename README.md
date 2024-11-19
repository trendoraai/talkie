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

## Configuration Priorities

Talkie uses a hierarchical configuration system, where settings are applied in the following order (highest priority first):

1. **Command-line Arguments**
   - Arguments passed directly to commands (e.g., `--api-key`, `--rag-dir`)
   - Override all other settings

2. **Chat File Frontmatter**
   - Settings in individual .md chat files
   - Applies only to that specific chat
   - Overrides global config and defaults

3. **Local Config File**
   - `config.talkie.yml` in the current directory
   - Project-specific settings

4. **Global Config File**
   - `~/.talkie/config.talkie.yml`
   - User-wide settings
   - Created automatically with defaults if not present

5. **Default Values**
   - Built-in defaults:
     ```yaml
     system_prompt: "You are a helpful AI assistant..."
     model: "gpt-4"
     api_endpoint: "https://api.openai.com/v1/chat/completions"
     rag_directory: ""
     ```

You can customize the global configuration by editing `~/.talkie/config.talkie.yml`, or create a local `config.talkie.yml` in your project directory for project-specific settings.

## Environment Variables

Talkie uses environment variables for sensitive information like API keys. The API key is looked up in the following order:

1. **Command-line Argument**
   - Passed via `--api-key` flag
   - Gets stored in `~/.talkie/.env` for future use
   - Highest priority

2. **Local .env File**
   - `.env` file in your current directory
   - Good for project-specific keys
   ```
   OPENAI_API_KEY=sk-your-key-here
   ```

3. **Environment Variable**
   - Set in your shell session
   ```bash
   # Mac/Linux
   export OPENAI_API_KEY=sk-your-key-here
   
   # Windows (PowerShell)
   $env:OPENAI_API_KEY='sk-your-key-here'
   ```

4. **Global .env File**
   - `~/.talkie/.env` file
   - Created automatically when using `--api-key`
   - Good for user-wide settings

If no API key is found, Talkie will display instructions for setting up your API key using any of these methods.

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
# Quick chat - Get immediate responses without creating chat files
talkie quick "What is the weather like today?"
talkie quick "Explain this code" --rag-dir ./src  # Include codebase context
talkie quick "Help me debug" --output debug.md    # Save conversation to file
talkie quick "Write a poem" --system "You are a poet"  # Custom system prompt

# Create a new chat file - Initialize a markdown file for ongoing conversations
talkie create python-help                    # Create python-help.md in current dir
talkie create code-review --dir ~/chats/work # Create in specific directory

# Ask questions in existing chats - Continue conversations in markdown files
talkie ask python-help.md                    # Use default API key from env/config
talkie ask code-review.md --api-key sk-xxx   # Use specific API key

# Additional Commands
talkie hey "Quick greeting"                  # Send a quick greeting
talkie bye                                   # End the conversation
```

Each chat file (.md) is initialized with frontmatter containing:
- Title and timestamps
- System prompt and model settings
- API endpoint configuration
- RAG directory settings
- Tags and summary fields

You can customize the chat behavior by editing the frontmatter section at the top of any chat file:
```yaml
---
title: python-help
system: You are a helpful Python programming assistant  # Change AI personality
model: gpt-4                                          # Switch between models
api_endpoint: https://api.openai.com/v1/chat/completions
rag_directory: ./src                                  # Add code context
created_at: 2024-01-20T10:30:00
updated_at: 2024-01-20T10:45:00
tags: [python, debugging]                            # Add organizational tags
summary: Debugging session for API implementation     # Add chat summary
---
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
