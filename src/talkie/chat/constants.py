FRONTMATTER_TEMPLATE = """---
title: {title}
system: {system}
rag_directory: {rag_directory}
model: {model}
api_endpoint: {api_endpoint}
created_at: {created_at}
updated_at: {updated_at}
tags: {tags}
summary: {summary}
---

user:"""

ADD_OPENAI_KEY_MESSAGE = """OpenAI API key not found! Please set it using one of these methods:
1. Run the command with your API key using --api-key=your-api-key-here
2. Set it in your .env file
3. Set it as an environment variable:
   - Windows (Command Prompt): set OPENAI_API_KEY=your-api-key-here
   - Windows (PowerShell): $env:OPENAI_API_KEY='your-api-key-here'
   - Mac/Linux: export OPENAI_API_KEY=your-api-key-here"""
