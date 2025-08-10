# Text Summarization API using FastAPI and LLaMA3 via Ollama
# This service accepts text, sends it to a local LLM, and returns a concise summary.
# It prevents hallucination and generation by using strict prompting and input validation.

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import requests
import logging

# -----------------------------------------------------------------------------
# Setup Logging
# -----------------------------------------------------------------------------
# Configure basic logging to track requests, errors, and model interactions
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Initialize FastAPI App
# -----------------------------------------------------------------------------
app = FastAPI(
    title="Text Summarizer API",
    description="A reliable summarization service using LLaMA3 via Ollama. Prevents AI from generating explanations.",
    version="1.0.0"
)

# -----------------------------------------------------------------------------
# Enable CORS (Cross-Origin Resource Sharing)
# -----------------------------------------------------------------------------
# Allow the Streamlit frontend (running on localhost:8501) to make requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],  # Only allow Streamlit app
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Define Request Data Structure
# -----------------------------------------------------------------------------
class SummarizeRequest(BaseModel):
    """
    Schema for incoming summarization requests.
    Ensures input is valid before processing.
    """
    text: str = Field(
        ...,  # Required field
        min_length=10,
        max_length=10000,
        description="The text to summarize. Must be 10–10,000 characters."
    )

# -----------------------------------------------------------------------------
# Health Check Endpoint
# -----------------------------------------------------------------------------
@app.get("/health")
def health_check():
    """
    Simple health endpoint to confirm the API is running.
    Useful for monitoring and debugging.
    """
    return {"status": "ok", "message": "Summarizer API is live"}

# -----------------------------------------------------------------------------
# Summarization Endpoint
# -----------------------------------------------------------------------------
@app.post("/summarize/")
def summarize(request: SummarizeRequest):
    """
    Main endpoint: receives text, validates it, sends to Ollama with a strict prompt,
    and returns a factual, concise summary — not a generated explanation.

    Args:
        request (SummarizeRequest): Validated input containing 'text'

    Returns:
        dict: {"summary": "generated summary text"}

    Raises:
        HTTPException: If validation, connection, or model errors occur
    """
    # Extract and clean input text
    input_text = request.text.strip()
    logger.info("Received new summarization request")

    # ✅ Additional Validation: Prevent summarization of short phrases or titles
    word_count = len(input_text.split())
    if word_count < 5:
        logger.warning(f"Input too short to summarize: '{input_text}' ({word_count} words)")
        raise HTTPException(
            status_code=400,
            detail="Input is too short to summarize. Please provide at least 5 words of content."
        )

    # ✅ Strict Prompt to Prevent AI from Explaining Instead of Summarizing
    prompt = f"""
You are a concise summarization engine. Your task is to shorten the following text into a brief,
factual summary while preserving key information, names, and intent.

Do NOT explain, expand, or invent details. Only compress the input.

Input text:
\"\"\"
{input_text}
\"\"\"

Summary (be clear, short, and objective):
""".strip()

    try:
        # Call local Ollama API
        ollama_response = requests.post(
            "http://localhost:11434/api/generate",  # Ollama's default URL
            json={
                "model": "llama3",  # ✅ Use LLaMA3 (better than llama2)
                "prompt": prompt,
                "stream": False  # Return full response at once
            },
            timeout=60  # Prevent hanging if Ollama is slow
        )

        # Check if Ollama responded successfully
        if ollama_response.status_code != 200:
            error_message = ollama_response.text
            logger.error(f"Ollama returned error: {error_message}")
            raise HTTPException(
                status_code=502,
                detail="Failed to communicate with Ollama. Check if it's running."
            )

        # Parse the JSON response from Ollama
        ollama_data = ollama_response.json()
        generated_summary = ollama_data.get("response", "").strip()

        # Ensure the model returned meaningful content
        if not generated_summary:
            logger.warning("Ollama returned empty response")
            raise HTTPException(
                status_code=500,
                detail="Model generated empty summary. Try again."
            )

        # Log success and return result
        logger.info("Summarization completed successfully")
        return {"summary": generated_summary}

    except requests.exceptions.ConnectionError:
        logger.error("Could not connect to Ollama. Is 'ollama serve' running?")
        raise HTTPException(
            status_code=503,
            detail="Cannot reach Ollama. Please start Ollama server."
        )

    except requests.exceptions.Timeout:
        logger.error("Request to Ollama timed out after 60 seconds")
        raise HTTPException(
            status_code=504,
            detail="Summarization took too long. Try a shorter text."
        )

    except Exception as unexpected_error:
        logger.error(f"Unexpected error during summarization: {unexpected_error}")
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred. Please try again."
        )