from __future__ import annotations

import json
from typing import Any

import numpy as np
import torch
from PIL import Image


def pil_to_tensor(img: Image.Image) -> torch.Tensor:
    # 必ず RGB に変換
    img = img.convert("RGB")

    arr = np.array(img).astype(np.float32) / 255.0
    # HWC のまま batch dimension を追加
    tensor = torch.from_numpy(arr)
    # Add batch dimension: (1, H, W, C)
    tensor = tensor.unsqueeze(0)
    return tensor


class MetainfoExtractor:
    """
    入力画像のメタデータから positive / negative を抽出するノード
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "path": ("STRING", {"default": ""}),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("image", "positive", "negative")
    FUNCTION = "extract"
    CATEGORY = "My Nodes"

    def extract(self, path) -> tuple[torch.Tensor, str, str]:
        pos_str: str = ""
        neg_str: str = ""

        img = Image.open(path)
        meta = img.info.get("prompt")
        prompt: dict[str, dict] = json.loads(meta)

        # Phase 1: KSampler から CLIP 入力元を記録
        pos_clip_idx = ""
        neg_clip_idx = ""
        for _, valdict in prompt.items():
            class_type: str = valdict.get("class_type")
            inputs: dict[str, Any] = valdict.get("inputs")
            if "KSampler" in class_type:
                pos_clip_idx = inputs.get("positive")[0]
                neg_clip_idx = inputs.get("negative")[0]
                break

        # Phase 2: 各 CLIP が直接入力されている場合は採用, さらに string 入力元がある場合は記録
        pos_str_idx = ""
        neg_str_idx = ""
        for idx, valdict in prompt.items():
            inputs: dict[str, Any] = valdict.get("inputs")
            text = inputs.get("text")
            if idx == pos_clip_idx:
                if isinstance(text, str):
                    pos_str = text
                else:
                    pos_str_idx = text[0]
            elif idx == neg_clip_idx:
                if isinstance(text, str):
                    neg_str = text
                else:
                    neg_str_idx = text[0]

        if pos_str and neg_str:
            return (pil_to_tensor(img), pos_str, neg_str)

        # Phase 3: string 入力元を採用(ShowText|pysssss のみ対応)
        for idx, valdict in prompt.items():
            inputs: dict[str, Any] = valdict.get("inputs")
            text = inputs.get("text_0")
            if idx == pos_str_idx and not pos_str:
                if isinstance(text, str):
                    pos_str = text
            elif idx == neg_str_idx and not neg_str:
                if isinstance(text, str):
                    neg_str = text

        return (pil_to_tensor(img), pos_str, neg_str)
