from __future__ import annotations

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


class UnlimitLoadImage:
    """
    任意のパスから画像をロードするノード
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "path": ("STRING", {"default": ""}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "extract"
    CATEGORY = "My Nodes"

    def extract(self, path) -> tuple[torch.Tensor]:
        return (pil_to_tensor(Image.open(path)),)
