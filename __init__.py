from __future__ import annotations

from .advanced_load_image import AdvancedLoadImage
from .advanced_save_image import AdvancedSaveImage
from .metainfo_extractor import MetainfoExtractor
from .unlimit_load_image import UnlimitLoadImage

NODE_CLASS_MAPPINGS = {
    "UnlimitLoadImage": UnlimitLoadImage,
    "MetainfoExtractor": MetainfoExtractor,
    "AdvancedSaveImage": AdvancedSaveImage,
    "AdvancedLoadImage": AdvancedLoadImage,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "UnlimitLoadImage": "UnlimitLoadImage",
    "MetainfoExtractor": "MetainfoExtractor",
    "AdvancedSaveImage": "AdvancedSaveImage",
    "AdvancedLoadImage": "AdvancedLoadImage",
}
