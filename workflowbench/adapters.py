"""Provider adapter interface and built-in adapters."""

from __future__ import annotations

import abc
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AdapterResponse:
    """Normalized response from any provider or agent."""

    text: str
    latency_ms: float
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""
    cost_usd: float = 0.0
    raw: dict[str, Any] = field(default_factory=dict)


class BaseAdapter(abc.ABC):
    """Interface every adapter must implement."""

    @abc.abstractmethod
    def execute(self, prompt: str, *, case_id: str = "") -> AdapterResponse:
        """Send a prompt and return a normalized response."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Human-readable adapter name."""


# ---------------------------------------------------------------------------
# OpenAI adapter
# ---------------------------------------------------------------------------

# Pricing per 1M tokens (approximate, gpt-4o as default)
_OPENAI_PRICING: dict[str, tuple[float, float]] = {
    "gpt-4o": (5.0, 15.0),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4-turbo": (10.0, 30.0),
    "gpt-3.5-turbo": (0.50, 1.50),
}


class OpenAIAdapter(BaseAdapter):
    """Adapter for OpenAI chat completions."""

    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
        system_prompt: str = "You are an enterprise workflow assistant. Follow instructions precisely.",
    ):
        self._model = model
        self._api_key = api_key
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._system_prompt = system_prompt

    @property
    def name(self) -> str:
        return f"openai/{self._model}"

    def execute(self, prompt: str, *, case_id: str = "") -> AdapterResponse:
        import openai

        client = openai.OpenAI(api_key=self._api_key) if self._api_key else openai.OpenAI()
        t0 = time.perf_counter()
        resp = client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=self._temperature,
            max_tokens=self._max_tokens,
        )
        latency = (time.perf_counter() - t0) * 1000
        usage = resp.usage
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0
        text = resp.choices[0].message.content or ""

        price_in, price_out = _OPENAI_PRICING.get(self._model, (5.0, 15.0))
        cost = (input_tokens * price_in + output_tokens * price_out) / 1_000_000

        return AdapterResponse(
            text=text,
            latency_ms=latency,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=self._model,
            cost_usd=cost,
            raw=resp.model_dump(),
        )


# ---------------------------------------------------------------------------
# Anthropic adapter
# ---------------------------------------------------------------------------

_ANTHROPIC_PRICING: dict[str, tuple[float, float]] = {
    "claude-sonnet-4-20250514": (3.0, 15.0),
    "claude-3-5-sonnet-20241022": (3.0, 15.0),
    "claude-3-haiku-20240307": (0.25, 1.25),
    "claude-3-opus-20240229": (15.0, 75.0),
}


class AnthropicAdapter(BaseAdapter):
    """Adapter for Anthropic messages API."""

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        api_key: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
        system_prompt: str = "You are an enterprise workflow assistant. Follow instructions precisely.",
    ):
        self._model = model
        self._api_key = api_key
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._system_prompt = system_prompt

    @property
    def name(self) -> str:
        return f"anthropic/{self._model}"

    def execute(self, prompt: str, *, case_id: str = "") -> AdapterResponse:
        import anthropic

        kwargs: dict[str, Any] = {}
        if self._api_key:
            kwargs["api_key"] = self._api_key
        client = anthropic.Anthropic(**kwargs)

        t0 = time.perf_counter()
        resp = client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            temperature=self._temperature,
            system=self._system_prompt,
            messages=[{"role": "user", "content": prompt}],
        )
        latency = (time.perf_counter() - t0) * 1000
        input_tokens = resp.usage.input_tokens
        output_tokens = resp.usage.output_tokens
        text = resp.content[0].text if resp.content else ""

        price_in, price_out = _ANTHROPIC_PRICING.get(self._model, (3.0, 15.0))
        cost = (input_tokens * price_in + output_tokens * price_out) / 1_000_000

        return AdapterResponse(
            text=text,
            latency_ms=latency,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=resp.model,
            cost_usd=cost,
            raw={"id": resp.id, "model": resp.model, "stop_reason": resp.stop_reason},
        )


# ---------------------------------------------------------------------------
# Echo adapter (for testing / offline use)
# ---------------------------------------------------------------------------

class EchoAdapter(BaseAdapter):
    """Returns the prompt back. Useful for testing the harness without API keys."""

    def __init__(self, prefix: str = "ECHO: "):
        self._prefix = prefix

    @property
    def name(self) -> str:
        return "echo"

    def execute(self, prompt: str, *, case_id: str = "") -> AdapterResponse:
        text = f"{self._prefix}{prompt}"
        return AdapterResponse(
            text=text,
            latency_ms=0.1,
            input_tokens=len(prompt.split()),
            output_tokens=len(text.split()),
            model="echo",
            cost_usd=0.0,
        )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

ADAPTERS: dict[str, type[BaseAdapter]] = {
    "openai": OpenAIAdapter,
    "anthropic": AnthropicAdapter,
    "echo": EchoAdapter,
}


def get_adapter(name: str, **kwargs: Any) -> BaseAdapter:
    """Instantiate an adapter by name."""
    cls = ADAPTERS.get(name)
    if cls is None:
        raise ValueError(f"Unknown adapter '{name}'. Available: {list(ADAPTERS.keys())}")
    return cls(**kwargs)
