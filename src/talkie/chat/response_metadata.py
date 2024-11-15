from datetime import datetime
import pytz
from typing import Dict, Any
import json


class ResponseMetadata:
    def __init__(self, model: str, id: str, created_formatted: str, total_tokens: int):
        self.model = model
        self.id = id
        self.created_formatted = created_formatted
        self.total_tokens = total_tokens

    @classmethod
    def from_response(cls, response_body: Dict[str, Any]) -> "ResponseMetadata":
        created = response_body.get("created", 0)
        created_datetime = datetime.fromtimestamp(created, tz=pytz.UTC)

        return cls(
            model=response_body.get("model", ""),
            id=response_body.get("id", ""),
            created_formatted=created_datetime.strftime("%Y-%m-%d %H:%M:%S %z"),
            total_tokens=response_body.get("usage", {}).get("total_tokens", 0),
        )


def write_metadata(file, metadata: ResponseMetadata) -> None:
    """Write metadata comments to a file."""
    file.write(f"<!-- model: {metadata.model} -->\n")
    file.write(f"<!-- id: {metadata.id} -->\n")
    file.write(f"<!-- created: {metadata.created_formatted} -->\n")
    file.write(f"<!-- total_tokens: {metadata.total_tokens} -->\n")


def handle_openai_response(
    file_path: str, question: str | None, answer: str, response_body: Dict[str, Any]
) -> None:
    """Handle OpenAI response and write to file."""
    with open(file_path, "a") as file:
        if question:
            file.write(f"\nPrompt with context -- \n{"\n".join(question).strip()}\n")

        file.write(f"\nassistant:\n{answer.strip()}\n")

        metadata = ResponseMetadata.from_response(response_body)
        write_metadata(file, metadata)

        if not question:
            file.write("\nuser:")
