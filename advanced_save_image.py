from __future__ import annotations

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
            "optional": {
                "clip_skip": ("INT", {"default": 0}),
                "positive": ("STRING", {"default": ""}),
                "negative": ("STRING", {"default": ""}),
                "seed": ("INT", {"default": 0}),
                "width": ("INT", {"default": 0}),
                "height": ("INT", {"default": 0}),
                "steps": ("INT", {"default": 0}),
                "cfg": ("FLOAT", {"default": 0.0}),
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

    def extract_metadata(
        self,
        clip_skip=0,
        positive="",
        negative="",
        seed=0,
        width=0,
        height=0,
        steps=0,
        cfg=0.0,
    ):
        metadata = {}

        if clip_skip != 0:
            metadata["clip_skip"] = clip_skip
        if positive:
            metadata["positive"] = positive
        if negative:
            metadata["negative"] = negative
        if seed != 0:
            metadata["seed"] = seed
        if width != 0:
            metadata["width"] = width
        if height != 0:
            metadata["height"] = height
        if steps != 0:
            metadata["steps"] = steps
        if cfg != 0.0:
            metadata["cfg"] = cfg

        return metadata

    def save_metadata_json(self, output_dir, image_metadata_dict):
        """メタデータをJSONファイルに保存"""
        meta_file = os.path.join(output_dir, "meta.json")

        # 既存のメタデータがあれば読み込む
        existing_data = {}
        if os.path.exists(meta_file):
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
            except Exception:
                pass

        # 新しいデータをマージ
        existing_data.update(image_metadata_dict)

        # JSONファイルに保存
        try:
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save metadata: {e}")

    def save_images(
        self,
        images,
        clip_skip=0,
        positive="",
        negative="",
        seed=0,
        width=0,
        height=0,
        steps=0,
        cfg=0.0,
        filename_prefix="ComfyUI",
        date_directory_format="%Y-%m-%d",
        prompt=None,
        extra_pnginfo=None,
    ):
        # メタデータを抽出
        metadata_dict = self.extract_metadata(
            clip_skip=clip_skip,
            positive=positive,
            negative=negative,
            seed=seed,
            width=width,
            height=height,
            steps=steps,
            cfg=cfg,
        )

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

        # filename_prefixからサブディレクトリとファイル名を分離
        # Windows/Linux両対応のため、両方の区切り文字をサポート
        filename_prefix = filename_prefix.replace("\\", "/")
        if "/" in filename_prefix:
            prefix_parts = filename_prefix.split("/")
            subdirs = "/".join(prefix_parts[:-1])
            filename_prefix = prefix_parts[-1]

            # サブディレクトリを作成
            output_dir = os.path.join(output_dir, subdirs)
            os.makedirs(output_dir, exist_ok=True)

            # subfolderパスを更新
            if use_date_dir:
                subfolder_prefix = os.path.join(date_str, subdirs)
            else:
                subfolder_prefix = subdirs
        else:
            subfolder_prefix = date_str if use_date_dir else ""

        filename_prefix += self.prefix_append

        full_output_folder, filename, counter, subfolder, filename_prefix = (
            folder_paths.get_save_image_path(
                filename_prefix, output_dir, images[0].shape[1], images[0].shape[0]
            )
        )

        # subfolderを更新
        if subfolder_prefix:
            if subfolder:
                subfolder = os.path.join(subfolder_prefix, subfolder)
            else:
                subfolder = subfolder_prefix

        results = list()
        image_metadata_dict = {}  # ファイル名をキーとしたメタデータ辞書

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
            file = f"{filename_with_batch_num}_{counter:05}_{seed}.png"
            img.save(
                os.path.join(full_output_folder, file),
                pnginfo=metadata,
                compress_level=self.compress_level,
            )

            # ファイル名をキーとしてメタデータを保存
            image_metadata_dict[file] = metadata_dict.copy()
            image_metadata_dict[file]["timestamp"] = datetime.now().isoformat()

            results.append({"filename": file, "subfolder": subfolder, "type": self.type})
            counter += 1

        # メタデータをJSONファイルに保存
        self.save_metadata_json(full_output_folder, image_metadata_dict)

        return {"ui": {"images": results}}
