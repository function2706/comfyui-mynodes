from __future__ import annotations

from .advanced_load_image import AdvancedLoadImage
from .advanced_save_image import AdvancedSaveImage
from .metainfo_extractor import MetainfoExtractor

NODE_CLASS_MAPPINGS = {
    "MetainfoExtractor": MetainfoExtractor,
    "AdvancedSaveImage": AdvancedSaveImage,
    "AdvancedLoadImage": AdvancedLoadImage,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MetainfoExtractor": "PNG Info Loader (DIY)",
    "AdvancedSaveImage": "AdvancedSaveImage",
    "AdvancedLoadImage": "AdvancedLoadImage",
}
