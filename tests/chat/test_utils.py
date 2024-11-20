import pytest
from typing import List, Dict, Any, Optional, Tuple
from talkie.chat.utils import (
    parse_file_content,
    parse_frontmatter_section,
    parse_messages_section,
    process_message_line,
    get_frontmatter_defaults,
    is_comment,
    is_file_reference,
    expand_file_reference,
)
import os
from unittest.mock import mock_open, patch


def test_parse_file_content_empty():
    """Test parsing empty file content."""
    content = ""
    with pytest.raises(
        ValueError, match="Invalid file format: Missing frontmatter section"
    ):
        parse_file_content(content, "test.md")


def test_parse_file_content_only_frontmatter():
    """Test parsing content with only frontmatter."""
    content = """---
system: Custom system prompt
model: gpt-3.5-turbo
---"""
    result = parse_file_content(content, "test.md")
    assert result == (
        "Custom system prompt",
        "gpt-3.5-turbo",
        "https://api.openai.com/v1/chat/completions",
        [],
        "",
    )


def test_parse_file_content_only_messages():
    """Test parsing content with only messages."""
    with pytest.raises(
        ValueError, match="Invalid file format: Missing frontmatter section"
    ):
        parse_file_content(
            """user: Hello
assistant: Hi there!""",
            "test.md",
        )


def test_parse_frontmatter_section():
    """Test parsing frontmatter section."""
    lines = [
        "system: Custom system prompt",
        "model: gpt-3.5-turbo",
        "api_endpoint: custom_endpoint",
        "rag_directory: /path/to/docs",
    ]
    result = parse_frontmatter_section(lines)
    assert result == {
        "system": "Custom system prompt",
        "model": "gpt-3.5-turbo",
        "api_endpoint": "custom_endpoint",
        "rag_directory": "/path/to/docs",
    }


def test_parse_frontmatter_section_multiline():
    """Test parsing frontmatter with multiline values."""
    lines = ["system: First line", " Second line", " Third line", "model: gpt-4"]
    result = parse_frontmatter_section(lines)
    assert result == {"system": "First line\nSecond line\nThird line", "model": "gpt-4"}


def test_parse_messages_section():
    """Test parsing messages section."""
    lines = [
        "user: Hello",
        "This is a multiline",
        "message",
        "assistant: Hi there!",
        "How can I help?",
    ]
    result = parse_messages_section(lines, "test.md")
    assert result == [
        {"role": "user", "content": ["Hello", "This is a multiline", "message"]},
        {"role": "assistant", "content": ["Hi there!", "How can I help?"]},
    ]


def test_parse_file_content_with_comments():
    """Test parsing content with HTML comments."""
    content = """---
system: Test system
---
user: Hello
<!-- this is a comment -->
assistant: Hi there!"""
    result = parse_file_content(content, "test.md")
    assert result[3] == [
        {"role": "user", "content": ["Hello"]},
        {"role": "assistant", "content": ["Hi there!"]},
    ]


def test_parse_file_content_multiline_messages():
    """Test parsing content with multiline messages."""
    content = """---
system: Test system
---
user: First line
second line
third line
assistant: Response line 1
response line 2"""
    result = parse_file_content(content, "test.md")
    assert result[3] == [
        {"role": "user", "content": ["First line", "second line", "third line"]},
        {"role": "assistant", "content": ["Response line 1", "response line 2"]},
    ]


def test_parse_file_content_empty_frontmatter_values():
    """Test handling of empty frontmatter values."""
    content = """---
system:
model:
---
user: Hello"""
    result = parse_file_content(content, "test.md")
    assert result[0] == "You are a helpful assistant."  # default value
    assert result[1] == "gpt-4"  # default value


def test_parse_file_content_whitespace_variations():
    """Test handling of various whitespace patterns."""
    content = """---
system:     Custom system prompt    
model:   gpt-4   
---
user:    Hello    
assistant:   Hi there!   """
    result = parse_file_content(content, "test.md")
    assert result[0] == "Custom system prompt"
    assert result[1] == "gpt-4"
    assert result[3] == [
        {"role": "user", "content": ["Hello"]},
        {"role": "assistant", "content": ["Hi there!"]},
    ]


def test_process_message_line_user():
    """Test processing user message line."""
    result = process_message_line(
        "user: Hello", {"role": None, "content": []}, "test.md"
    )
    assert result == {"role": "user", "content": ["Hello"]}


def test_process_message_line_assistant():
    """Test processing assistant message line."""
    result = process_message_line(
        "assistant: Hi", {"role": None, "content": []}, "test.md"
    )
    assert result == {"role": "assistant", "content": ["Hi"]}


def test_get_frontmatter_defaults_empty():
    """Test getting frontmatter defaults with empty input."""
    result = get_frontmatter_defaults({})
    assert result == (
        "You are a helpful assistant.",
        "gpt-4",
        "https://api.openai.com/v1/chat/completions",
        "",
    )


def test_is_comment_valid():
    """Test valid HTML comment detection."""
    assert is_comment("<!-- comment -->") is True


def test_is_comment_invalid():
    """Test invalid HTML comment detection."""
    assert is_comment("< !-- not a comment -->") is False
    assert is_comment("<!-- incomplete") is False
    assert is_comment("not a comment -->") is False


def test_is_file_reference_valid():
    """Test valid file reference detection."""
    assert is_file_reference("[[file.txt]]") is True


def test_is_file_reference_invalid():
    """Test invalid file reference detection."""
    assert is_file_reference("[file.txt]") is False
    assert is_file_reference("[[file.txt") is False
    assert is_file_reference("file.txt]]") is False
