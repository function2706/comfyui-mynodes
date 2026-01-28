import json
import os
import re
from datetime import datetime

import folder_paths
import numpy as np
from comfy.cli_args import args
from PIL import Image
from PIL.PngImagePlugin import PngInfo


class AdvancedSaveImage:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.prefix_append = ""
        self.compress_level = 4

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE", {"tooltip": "The images to save."}),
                "filename_prefix": (
                    "STRING",
                    {
                        "default": "ComfyUI",
                        "tooltip": "The prefix for the file to save.",
                    },
                ),
                "date_directory_format": (
                    "STRING",
                    {
                        "default": "%Y-%m-%d",
                        "tooltip": "Date format for directory name."
                        + " Use Python strftime format (%Y,%m,%d)."
                        + " Leave empty to disable date directory.",
                    },
                ),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ()
    FUNCTION = "save_images"

    OUTPUT_NODE = True

    CATEGORY = "My Nodes"
    DESCRIPTION = "Saves the input images to your ComfyUI output directory."

    def process_date_format(self, text):
        """テキスト内の日付フォーマット(%Y-%m-%d等)を実際の日付に置換"""

        def replace_date_format(match):
            format_str = match.group(0)
            try:
                return datetime.now().strftime(format_str)
            except Exception:
                return format_str

        # %で始まる日付フォーマットパターンを検出して置換
        # strftimeで使用可能なパターンをマッチング
        pattern = r"%[YymbBdHIMSpjaAwUWcxXzZ%+-]+"
        result = re.sub(pattern, replace_date_format, text)
        return result

    def save_images(
        self,
        images,
        filename_prefix="ComfyUI",
        date_directory_format="%Y-%m-%d",
        prompt=None,
        extra_pnginfo=None,
    ):
        # 日付ディレクトリの作成(フォーマットが指定されている場合)
        if date_directory_format.strip():
            date_str = self.process_date_format(date_directory_format)
            output_dir = os.path.join(self.output_dir, date_str)
            os.makedirs(output_dir, exist_ok=True)
            use_date_dir = True
        else:
            output_dir = self.output_dir
            use_date_dir = False

        # filename_prefixの日付フォーマットを処理
        filename_prefix = self.process_date_format(filename_prefix)
        filename_prefix += self.prefix_append

        full_output_folder, filename, counter, subfolder, filename_prefix = (
            folder_paths.get_save_image_path(
                filename_prefix, output_dir, images[0].shape[1], images[0].shape[0]
            )
        )

        # subfolderに日付ディレクトリを含める
        if use_date_dir:
            if subfolder:
                subfolder = os.path.join(date_str, subfolder)
            else:
                subfolder = date_str

        results = list()
        for batch_number, image in enumerate(images):
            i = 255.0 * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
            metadata = None
            if not args.disable_metadata:
                metadata = PngInfo()
                if prompt is not None:
                    metadata.add_text("prompt", json.dumps(prompt))
                if extra_pnginfo is not None:
                    for x in extra_pnginfo:
                        metadata.add_text(x, json.dumps(extra_pnginfo[x]))

            filename_with_batch_num = filename.replace("%batch_num%", str(batch_number))
            file = f"{filename_with_batch_num}_{counter:05}_.png"
            img.save(
                os.path.join(full_output_folder, file),
                pnginfo=metadata,
                compress_level=self.compress_level,
            )
            results.append({"filename": file, "subfolder": subfolder, "type": self.type})
            counter += 1

        return {"ui": {"images": results}}
