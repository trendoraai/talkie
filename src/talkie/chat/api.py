import logging
import httpx
import json
from typing import Tuple, Dict, Any, List


async def query_openai(
    api_key: str, model: str, api_endpoint: str, messages: List[Dict[str, Any]]
) -> Tuple[str, Dict[str, Any]]:
    """
    Query the OpenAI API with the provided parameters.

    Returns:
        Tuple containing (answer string, full response body)
    """
    logging.info(f"Sending request to OpenAI API using model: {model}")
    logging.debug(
        f"Request payload:\n{json.dumps({'model': model, 'messages': messages}, indent=2)}"
    )

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
        logging.debug(f"Received response:\n{json.dumps(response_body, indent=2)}")

        answer = response_body["choices"][0]["message"]["content"]
        logging.info("Successfully received and parsed answer from OpenAI API")

        return answer, response_body
