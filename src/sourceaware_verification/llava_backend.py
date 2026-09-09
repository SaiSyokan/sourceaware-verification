"""Thin adapter for an externally installed upstream LLaVA implementation."""

from __future__ import annotations

import random
from pathlib import Path


class LlavaBackend:
    def __init__(
        self,
        model_path: str,
        model_base: str | None = None,
        conversation_mode: str | None = None,
        temperature: float = 0.0,
        top_p: float | None = None,
        num_beams: int = 1,
        max_new_tokens: int = 512,
        seed: int = 42,
    ) -> None:
        try:
            import torch
            from llava.mm_utils import get_model_name_from_path
            from llava.model.builder import load_pretrained_model
        except ImportError as exc:
            raise RuntimeError(
                "Install the upstream LLaVA package and the inference extra before use"
            ) from exc
        self.torch = torch
        self.temperature = temperature
        self.top_p = top_p
        self.num_beams = num_beams
        self.max_new_tokens = max_new_tokens
        model_name = get_model_name_from_path(model_path)
        self.conversation_mode = conversation_mode or self._conversation_mode(model_name)
        random.seed(seed)
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        loaded = load_pretrained_model(model_path, model_base, model_name)
        self.tokenizer, self.model, self.image_processor, self.context_length = loaded

    @staticmethod
    def _conversation_mode(model_name: str) -> str:
        normalized = model_name.lower()
        if "v1.6-34b" in normalized:
            return "chatml_direct"
        if "llama-2" in normalized:
            return "llava_llama_2"
        if "mistral" in normalized:
            return "mistral_instruct"
        if "v1" in normalized:
            return "llava_v1"
        if "mpt" in normalized:
            return "mpt"
        return "llava_v0"

    def generate(self, prompt: str, image_path: str | Path | None = None) -> str:
        from llava.constants import DEFAULT_IMAGE_TOKEN, IMAGE_TOKEN_INDEX
        from llava.conversation import conv_templates
        from llava.mm_utils import process_images, tokenizer_image_token

        image_tensor = None
        image_sizes = None
        if image_path is not None:
            from PIL import Image

            with Image.open(image_path) as opened:
                image = opened.convert("RGB")
                image_sizes = [image.size]
                image_tensor = process_images([image], self.image_processor, self.model.config)
            dtype = getattr(self.model, "dtype", self.torch.float32)
            if isinstance(image_tensor, list):
                image_tensor = [item.to(device=self.model.device, dtype=dtype) for item in image_tensor]
            else:
                image_tensor = image_tensor.to(device=self.model.device, dtype=dtype)
            prompt = DEFAULT_IMAGE_TOKEN + "\n" + prompt

        conversation = conv_templates[self.conversation_mode].copy()
        conversation.append_message(conversation.roles[0], prompt)
        conversation.append_message(conversation.roles[1], None)
        input_ids = tokenizer_image_token(
            conversation.get_prompt(), self.tokenizer, IMAGE_TOKEN_INDEX, return_tensors="pt"
        ).unsqueeze(0).to(self.model.device)
        kwargs = {
            "input_ids": input_ids,
            "do_sample": self.temperature > 0,
            "temperature": self.temperature,
            "num_beams": self.num_beams,
            "max_new_tokens": self.max_new_tokens,
            "use_cache": True,
        }
        if self.top_p is not None:
            kwargs["top_p"] = self.top_p
        if image_tensor is not None:
            kwargs.update({"images": image_tensor, "image_sizes": image_sizes})
        with self.torch.inference_mode():
            output_ids = self.model.generate(**kwargs)
        generated = output_ids[:, input_ids.shape[1] :]
        return self.tokenizer.batch_decode(generated, skip_special_tokens=True)[0].strip()

