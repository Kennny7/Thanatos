# Thanatos\services\local_llm\tool_parser.py
import json
import re
import logging

from shared.logging_setup import ensure_logging

ensure_logging()
logger = logging.getLogger(__name__)


def extract_json(content: str):
    """
    Extract JSON from raw model output.
    Handles ```json ... ``` wrappers.
    Also attempts fallback extraction for inline JSON.
    """
    logger.debug("Extracting JSON from model output")

    # Case 1: Markdown ```json block
    match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
    if match:
        logger.debug("Markdown JSON block detected, extracting inner content")
        content = match.group(1)
    else:
        logger.debug("No markdown JSON block detected")

        # Case 2: Try to extract first JSON object heuristically
        brace_match = re.search(r"\{.*\}", content, re.DOTALL)
        if brace_match:
            logger.debug("Inline JSON detected, extracting first JSON object")
            content = brace_match.group(0)

    cleaned = content.strip()
    logger.debug("Extracted JSON preview: %s", cleaned[:200])

    return cleaned


def normalize_args(data: dict):
    """
    Normalize different argument formats into dict.
    """
    logger.debug("Normalizing arguments format")

    # Case 1: already correct
    if "args" in data and isinstance(data["args"], dict):
        logger.debug("Arguments already in correct format")
        return data

    # Case 2: OpenAI-style
    if "arguments" in data:
        args = data["arguments"]
        logger.debug("Found 'arguments' field of type: %s", type(args).__name__)

        # If dict → rename
        if isinstance(args, dict):
            data["args"] = args
            logger.debug("Converted dict arguments to 'args'")
            return data

        # If string → attempt JSON parse
        if isinstance(args, str):
            try:
                parsed_args = json.loads(args)
                if isinstance(parsed_args, dict):
                    data["args"] = parsed_args
                    logger.debug("Parsed string arguments into dict")
                    return data
            except Exception:
                logger.debug("Failed to parse string arguments as JSON")

        # If list → map heuristically
        if isinstance(args, list):
            logger.debug("Mapping list arguments heuristically")
            data["args"] = {"location": args[0]} if args else {}
            return data

    logger.debug("No argument normalization applied")
    return data


def parse_llm_output(content: str):
    logger.info("Parsing LLM output")

    try:
        cleaned = extract_json(content)

        logger.debug("Attempting JSON load")
        data = json.loads(cleaned)

        logger.debug("JSON parsed successfully")

        data = normalize_args(data)

        logger.info("LLM output parsed into structured action")
        return data

    except Exception:
        logger.exception("Primary JSON parsing failed, attempting recovery")

        # Secondary attempt: try extracting JSON again (more aggressive)
        try:
            brace_match = re.search(r"\{.*\}", content, re.DOTALL)
            if brace_match:
                logger.debug("Recovery attempt: extracting JSON block again")
                data = json.loads(brace_match.group(0))
                data = normalize_args(data)

                logger.info("Recovered JSON parsing successfully")
                return data
        except Exception:
            logger.debug("Recovery attempt failed")

        logger.exception("Failed to parse LLM output, falling back to text response")

        return {
            "action": "respond",
            "text": content.strip()
        }