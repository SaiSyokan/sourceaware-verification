"""Language-only generation backend for text verification and aggregation."""

from __future__ import annotations

import random
from pathlib import Path


class HFCausalLMBackend:
    """Thin Hugging Face causal-LM adapter used for language-only calls.

    The zero-shot image-text instantiation in the manuscript uses an LVLM for
    image-conditioned operations and an LLM for language-only operations. This
    adapter covers verification-question generation, text veracity,
    image-text consistency after image description, and aggregation.
    """

    def __init__(
        self,
        model_path: str,
        *,
        tokenizer_path: str | None = None,
        device_map: str | None = "auto",
        trust_remote_code: bool = False,
        temperature: float = 0.0,
        top_p: float | None = None,
        num_beams: int = 1,
        max_new_tokens: int = 512,
        seed: int = 42,
    ) -> None:
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError(
                "Install the inference extra before using the language backend: "
                "pip install -e '.[inference]'"
            ) from exc

        self.torch = torch
        self.temperature = temperature
        self.top_p = top_p
        self.num_beams = num_beams
        self.max_new_tokens = max_new_tokens

        random.seed(seed)
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

        tokenizer_source = tokenizer_path or model_path
        self.tokenizer = AutoTokenizer.from_pretrained(
            tokenizer_source,
            trust_remote_code=trust_remote_code,
            use_fast=False,
        )
        if self.tokenizer.pad_token_id is None and self.tokenizer.eos_token is not None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            device_map=device_map,
            torch_dtype="auto",
            trust_remote_code=trust_remote_code,
        )
        self.model.eval()

    def _format_prompt(self, prompt: str):
        messages = [{"role": "user", "content": prompt}]
        chat_template = getattr(self.tokenizer, "chat_template", None)
        if chat_template:
            return self.tokenizer.apply_chat_template(
                messages,
                add_generation_prompt=True,
                return_tensors="pt",
            )
        return self.tokenizer(prompt, return_tensors="pt").input_ids

    def generate(self, prompt: str, image_path: str | Path | None = None) -> str:
        if image_path is not None:
            raise ValueError("HFCausalLMBackend is language-only and does not accept images")

        input_ids = self._format_prompt(prompt)
        device = next(self.model.parameters()).device
        input_ids = input_ids.to(device)
        attention_mask = self.torch.ones_like(input_ids)

        kwargs = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "do_sample": self.temperature > 0,
            "num_beams": self.num_beams,
            "max_new_tokens": self.max_new_tokens,
            "use_cache": True,
        }
        if self.temperature > 0:
            kwargs["temperature"] = self.temperature
        if self.top_p is not None:
            kwargs["top_p"] = self.top_p

        with self.torch.inference_mode():
            output_ids = self.model.generate(**kwargs)
        generated = output_ids[:, input_ids.shape[1] :]
        return self.tokenizer.batch_decode(generated, skip_special_tokens=True)[0].strip()
