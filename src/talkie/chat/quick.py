import asyncio
from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from .api import query_openai
from .constants import FRONTMATTER_TEMPLATE
from .response_metadata import handle_openai_response
from .ask import get_openai_api_key, discover_rag_path


async def quick_chat(
    question: str,
    system_prompt: Optional[str] = None,
    model: str = "gpt-3.5-turbo",
    api_endpoint: str = "https://api.openai.com/v1/chat/completions",
    api_key: Optional[str] = None,
    output_file: Optional[str] = None,
    rag_directory: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Quickly send a question to OpenAI without creating a chat file.
    If output_file is provided, the conversation will be saved to that file.

    Args:
        question: The question to ask
        system_prompt: Optional system prompt
        model: The model to use
        api_endpoint: The API endpoint
        api_key: Optional API key
        output_file: Optional output file to save the conversation
        rag_directory: Optional directory to use for RAG context
    """
    try:
        api_key = get_openai_api_key(api_key)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # If RAG directory is provided, augment the question with relevant context
        full_question = question
        if rag_directory:
            from ..rag.directory_rag import DirectoryRAG

            rag = DirectoryRAG(rag_directory)
            rag_context = rag.query(question)
            if rag_context:
                full_question = (
                    f"Context from codebase:\n{rag_context}\n\nQuestion: {question}"
                )

        messages.append({"role": "user", "content": full_question})

        answer, response_body = await query_openai(
            api_key, model, api_endpoint, messages
        )

        if output_file:
            save_quick_chat(
                output_file,
                question,
                answer,
                response_body,
                system_prompt,
                model,
                api_endpoint,
                rag_directory,
            )

        return {"answer": answer, "response": response_body}

    except Exception as e:
        logging.error(f"Error in quick chat: {str(e)}")
        raise


def save_quick_chat(
    file_path: str,
    question: str,
    answer: str,
    response_body: Dict[str, Any],
    system_prompt: Optional[str],
    model: str,
    api_endpoint: str,
    rag_directory: Optional[str] = None,
) -> None:
    """Save the quick chat to a file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    frontmatter = FRONTMATTER_TEMPLATE.format(
        timestamp=timestamp,
        model=model,
        api_endpoint=api_endpoint,
        system_prompt=system_prompt if system_prompt else "",
    )

    # Add rag_directory to frontmatter if provided
    if rag_directory:
        frontmatter += f"rag_directory: {rag_directory}\n"
    frontmatter += "---\n\n"

    content = f"{frontmatter}" f"user: {question}\n\n" f"assistant: {answer}\n"

    metadata = handle_openai_response(response_body)
    if metadata:
        content += f"\nmetadata: {json.dumps(metadata, indent=2)}\n"

    with open(file_path, "w") as f:
        f.write(content)
