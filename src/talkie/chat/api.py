import httpx
import json
from typing import Tuple, Dict, Any, List
from talkie.logger_setup import talkie_logger as logging


async def query_openai(
    api_key: str, model: str, api_endpoint: str, messages: List[Dict[str, Any]]
) -> Tuple[str, Dict[str, Any]]:
    """
    Query the OpenAI API with the provided parameters.

    Returns:
        Tuple containing (answer string, full response body)
    """
    logging.info(f"Sending request to OpenAI API using model: {model}")
    json_string = json.dumps(
        {"model": model, "messages": messages}, indent=2, ensure_ascii=False
    )

    # Replace escaped newlines with actual newlines
    formatted_json_string = json_string.replace("\\n", "\n")
    logging.debug(f"Request payload:\n{formatted_json_string}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            api_endpoint,
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": model, "messages": messages},
        )

        if not response.is_success:
            raise Exception(
                f"OpenAI API error (status {response.status_code}): {response.text}"
            )

        response_body = response.json()
        json_string = json.dumps(response_body, indent=2, ensure_ascii=False)

        # Replace escaped newlines with actual newlines
        formatted_json_string = json_string.replace("\\n", "\n")
        logging.debug(f"Received response:\n{formatted_json_string}")

        answer = response_body["choices"][0]["message"]["content"]
        logging.info("Successfully received and parsed answer from OpenAI API")

        return answer, response_body
