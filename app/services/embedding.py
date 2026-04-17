from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

import httpx
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

from app.core.config import get_settings


class _OnnxEmbedder:
    def __init__(self, model_path: str, tokenizer_path: str) -> None:
        self.np = np
        self.session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
        self.tokenizer = Tokenizer.from_file(tokenizer_path)

    def embed(self, text: str) -> list[float]:
        encoded = self.tokenizer.encode(text)
        input_ids = self.np.array([encoded.ids], dtype=self.np.int64)
        attention_mask = self.np.array([encoded.attention_mask], dtype=self.np.int64)

        outputs = self.session.run(
            None,
            {
                "input_ids": input_ids,
                "attention_mask": attention_mask,
            },
        )
        last_hidden_state = outputs[0]

        # Masked mean pooling gives more stable vectors than averaging padded tokens.
        expanded_mask = attention_mask[..., None].astype(last_hidden_state.dtype)
        pooled = (last_hidden_state * expanded_mask).sum(axis=1) / self.np.clip(
            expanded_mask.sum(axis=1),
            1e-9,
            None,
        )
        return pooled[0].astype(self.np.float32).tolist()


@lru_cache
def _get_onnx_embedder() -> _OnnxEmbedder:
    settings = get_settings()
    return _OnnxEmbedder(
        model_path=settings.embedding_onnx_model_path,
        tokenizer_path=settings.embedding_onnx_tokenizer_path,
    )


def _extract_embedding(payload: Any) -> list[float]:
    if isinstance(payload, list):
        values: Any = payload

        # Some providers return a single nested vector like [[...]]
        if len(values) == 1 and isinstance(values[0], (list, tuple, str)):
            values = values[0]

        # Some providers wrap the vector as a JSON string.
        if isinstance(values, str):
            try:
                values = json.loads(values)
            except json.JSONDecodeError as exc:
                raise RuntimeError("Embedding response format is not supported.") from exc

        if isinstance(values, (list, tuple)):
            return [float(str(value)) for value in values]

        raise RuntimeError("Embedding response format is not supported.")
    if isinstance(payload, dict) and payload.get("data"):
        return [float(str(value)) for value in payload["data"][0]["embedding"]]
    raise RuntimeError("Embedding response format is not supported.")


def _generate_embedding_http(text: str) -> list[float]:
    settings = get_settings()
    timeout = httpx.Timeout(settings.embedding_timeout_seconds)

    with httpx.Client(base_url=settings.embedding_service_url, timeout=timeout) as client:
        response = client.post("/embed", json={"inputs": text, "truncate": True})

        if response.status_code in {404, 405}:
            response = client.post(
                "/v1/embeddings",
                json={"input": [text], "model": settings.embedding_model_name},
            )

        response.raise_for_status()
        return _extract_embedding(response.json())


def generate_embedding(text: str) -> list[float]:
    settings = get_settings()
    provider = settings.embedding_provider.lower().strip()

    if provider == "onnx":
        return _get_onnx_embedder().embed(text)

    return _generate_embedding_http(text)
