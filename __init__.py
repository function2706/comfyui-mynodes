from .advanced_save_image import AdvancedSaveImage
from .metainfo_extractor import MetainfoExtractor

NODE_CLASS_MAPPINGS = {
    "MetainfoExtractor": MetainfoExtractor,
    "AdvancedSaveImage": AdvancedSaveImage,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MetainfoExtractor": "PNG Info Loader (DIY)",
    "AdvancedSaveImage": "AdvancedSaveImage",
}
