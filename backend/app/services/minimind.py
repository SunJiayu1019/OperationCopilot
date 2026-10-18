import json
import os
import sys
from pathlib import Path
from typing import Any, Callable

from PIL import Image
from pydantic import ValidationError

from .errors import ModelConfigurationError, ModelOutputError
from .schemas import VisualAnalysis


class MiniMindVAdapter:
    def __init__(self, model: Any | None = None, tokenizer: Any | None = None, processor: Any | None = None, device: str | None = None, model_root: Path | None = None) -> None:
        self.device = device or os.getenv("MINIMIND_DEVICE", "cpu")
        self.model_root = model_root or Path(__file__).resolve().parents[3] / "minimind-v"
        self.model = model
        self.tokenizer = tokenizer
        self.processor = processor
        if model is None:
            self._load()

    def _load(self) -> None:
        try:
            import sys
            import torch
            root = str(self.model_root)
            if root not in sys.path:
                sys.path.insert(0, root)
            from model.model_vlm import MiniMindVLM, VLMConfig
            tokenizer_path = self.model_root / "model"
            vision_path = self.model_root / "model" / "siglip2-base-p32-256-ve"
            checkpoint = self.model_root / "out" / "sft_vlm_768.pth"
            if not tokenizer_path.exists() or not vision_path.exists() or not checkpoint.exists():
                raise ModelConfigurationError(f"MiniMind-V resources are incomplete under {self.model_root}")
            self.tokenizer = __import__("transformers").AutoTokenizer.from_pretrained(tokenizer_path, trust_remote_code=True)
            self.model = MiniMindVLM(VLMConfig(hidden_size=768, num_hidden_layers=8, use_moe=False), vision_model_path=str(vision_path))
            state_dict = torch.load(checkpoint, map_location=self.device)
            self.model.load_state_dict({key: value for key, value in state_dict.items() if "mask" not in key}, strict=False)
            self.model = self.model.eval().to(self.device)
            if hasattr(self.model, "processor"):
                self.processor = self.model.processor
        except ModelConfigurationError:
            raise
        except Exception as error:
            raise ModelConfigurationError(f"Unable to load MiniMind-V: {error}") from error

    def analyze(self, image_path: Path, prompt: str, structurer: Callable[[str], dict[str, Any]] | None = None) -> dict[str, Any]:
        if not image_path.exists():
            raise FileNotFoundError(image_path)
        image = Image.open(image_path).convert("RGB")
        if self.processor is None or self.model is None or self.tokenizer is None:
            raise ModelConfigurationError("MiniMind-V adapter is not initialized")
        import torch
        if str(self.model_root) not in sys.path:
            sys.path.insert(0, str(self.model_root))
        from model.model_vlm import MiniMindVLM
        pixel_values = {key: value.to(self.device) for key, value in MiniMindVLM.image2tensor(image, self.processor).items()}
        image_token = self.model.config.image_special_token * self.model.config.image_token_len
        messages = [{"role": "user", "content": f"{image_token}\n{prompt}"}]
        text = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer(text, return_tensors="pt")
        inputs = {key: value.to(self.device) for key, value in inputs.items()}
        with torch.inference_mode():
            generated = self.model.generate(inputs=inputs["input_ids"], attention_mask=inputs.get("attention_mask"), max_new_tokens=512, do_sample=False, pad_token_id=self.tokenizer.pad_token_id, eos_token_id=self.tokenizer.eos_token_id, pixel_values=pixel_values)
        raw = generated if isinstance(generated, str) else self.tokenizer.decode(generated[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        if not raw.strip():
            raise ModelOutputError("MiniMind-V returned no visual description")
        structured = False
        try:
            result = json.loads(raw)
        except json.JSONDecodeError as error:
            if structurer is None:
                raise ModelOutputError("MiniMind-V returned invalid JSON and no text structurer is configured") from error
            result = structurer(raw)
            structured = True
        try:
            return {**VisualAnalysis.model_validate(result).model_dump(), "raw_description": raw}
        except ValidationError as error:
            if structurer is None or structured:
                raise ModelOutputError("MiniMind-V output lacks required visual fields") from error
            try:
                return {**VisualAnalysis.model_validate(structurer(raw)).model_dump(), "raw_description": raw}
            except ValidationError as structuring_error:
                raise ModelOutputError("Structured visual output lacks required fields") from structuring_error
