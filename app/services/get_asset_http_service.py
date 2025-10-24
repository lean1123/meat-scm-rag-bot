from typing import Dict, Any
import requests

from dotenv import load_dotenv
import os

# Load env variables from .env file if needed
load_dotenv()

BASE_URL = os.getenv("BASE_URL")


def get_asset_trace(asset_id: str,
                    timeout: int = 5,
                    max_retries: int = 3) -> Dict[str, Any]:
    """Fetch the asset trace data from the external trace API and return it as a Python dict.

    Args:
        asset_id: the asset id to query (will be substituted into the URL path).
        timeout: per-request timeout in seconds.
        max_retries: number of attempts before giving up on network errors.

    Returns:
        The parsed JSON response as a Python dict.

    Raises:
        ValueError: if `asset_id` is empty.
        requests.HTTPError: if the remote service returns a non-200 response.
        requests.RequestException: for network-related errors after retries are exhausted.
    """

    if not asset_id or not isinstance(asset_id, str):
        raise ValueError("asset_id must be a non-empty string")

    url = f"{BASE_URL}/assets/{asset_id}/trace"

    last_exception = None
    # Use a session context manager so it is closed properly
    with requests.Session() as session:
        for attempt in range(1, max_retries + 1):
            try:
                resp = session.get(url, timeout=timeout)
                # Raise for HTTP errors other than 2xx
                if resp.status_code == 200:
                    # Return parsed JSON as dict
                    return resp.json()
                else:
                    # try to include body in the error message
                    msg = f"Unexpected status code: {resp.status_code}. Response body: {resp.text}"
                    http_err = requests.HTTPError(msg, response=resp)
                    raise http_err
            except requests.RequestException as exc:
                last_exception = exc
                # If we have more retries, continue; otherwise re-raise
                if attempt < max_retries:
                    # simple backoff: continue to next attempt

                    continue
                else:
                    # Exhausted retries
                    raise
    # If somehow we exit loop without returning, raise the last exception
    if last_exception:
        raise last_exception
    # Fallback (should not be reached)
    raise requests.RequestException("Failed to fetch asset trace for unknown reasons")


# Example usage:
if __name__ == "__main__":
    test_asset_id = "FARM-PORK-20251024-YC6R"
    try:
        trace_data = get_asset_trace(test_asset_id)
        print("Asset Trace Data:", trace_data)
    except Exception as e:
        print("Error fetching asset trace:", str(e))
