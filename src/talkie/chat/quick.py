from datetime import datetime
import json
from typing import Optional, Dict, Any
from pathlib import Path

from talkie.chat.api import query_openai
from talkie.chat.constants import FRONTMATTER_TEMPLATE
from talkie.chat.response_metadata import handle_openai_response
from talkie.chat.ask import get_openai_api_key
from talkie.chat.create import create_chat
from talkie.logger_setup import talkie_logger as logging
from talkie.rag.directory_rag import DirectoryRAG


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
            api_key = get_openai_api_key(api_key)
            rag = DirectoryRAG(rag_directory, openai_api_key=api_key)
            rag.process_directory()
            rag_context = []
            for filename, content in rag.query(question):
                context = f"File Path: {filename}\nFile Content:\n{content}\n"
                rag_context.append(context)

            if rag_context:
                text_rag_context = "\n".join(rag_context)
                full_question = f"Context from codebase:\n{text_rag_context}\n\nQuestion: {question}"

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
    path = Path(file_path)

    # Create the chat file with frontmatter
    create_chat(path.stem, str(path.parent))

    # Let handle_openai_response append the conversation and metadata
    handle_openai_response(file_path, question, answer, response_body)
