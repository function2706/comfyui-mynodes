from __future__ import annotations

import hashlib
import json
import os
import sys

import folder_paths
import node_helpers
import numpy as np
import torch
from PIL import Image, ImageOps, ImageSequence

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "comfy"))


def get_holderpath(filename: str, base_dir: str) -> str | None:
    """
    output 以下を探索し, 指定ファイルを含むディレクトリ名だけ返す\n
    見つからなければ None
    """
    for root, _, files in os.walk(base_dir):
        if filename in files:
            return root
    return None


class AdvancedLoadImage:
    @classmethod
    def INPUT_TYPES(s):
        input_dir = folder_paths.get_input_directory()
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
        files = folder_paths.filter_files_content_types(files, ["image"])
        return {
            "required": {"image": (sorted(files), {"image_upload": True})},
        }

    CATEGORY = "My Nodes"

    RETURN_TYPES = ("IMAGE", "MASK", "INT", "STRING", "STRING", "INT", "INT", "INT", "INT", "FLOAT")
    RETURN_NAMES = (
        "IMAGE",
        "MASK",
        "clip_skip",
        "positive",
        "negative",
        "seed",
        "width",
        "height",
        "steps",
        "cfg",
    )
    FUNCTION = "load_image"

    def load_metadata(self, image_filename):
        """Load metadata from meta.json for the given image filename"""
        output_dir = folder_paths.get_output_directory()
        dirpath = get_holderpath(image_filename, output_dir)

        meta_path = os.path.join(dirpath, "meta.json")

        # Default values
        metadata = {
            "clip_skip": 0,
            "positive": "",
            "negative": "",
            "seed": 0,
            "width": 0,
            "height": 0,
            "steps": 0,
            "cfg": 0.0,
        }

        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta_data = json.load(f)

                # Search for the image_path key matching the current image
                if image_filename in meta_data:
                    meta = meta_data[image_filename]
                    metadata["clip_skip"] = meta.get("clip_skip", 0)
                    metadata["positive"] = meta.get("positive", "")
                    metadata["negative"] = meta.get("negative", "")
                    metadata["seed"] = meta.get("seed", 0)
                    metadata["width"] = meta.get("width", 0)
                    metadata["height"] = meta.get("height", 0)
                    metadata["steps"] = meta.get("steps", 0)
                    metadata["cfg"] = meta.get("cfg", 0.0)
            except Exception as e:
                print(f"Error loading meta.json: {e}")

        return metadata

    def load_image(self, image):
        image_path = folder_paths.get_annotated_filepath(image)

        # Load image
        img = node_helpers.pillow(Image.open, image_path)

        output_images = []
        output_masks = []
        w, h = None, None

        for i in ImageSequence.Iterator(img):
            i = node_helpers.pillow(ImageOps.exif_transpose, i)

            if i.mode == "I":
                i = i.point(lambda i: i * (1 / 255))
            image_data = i.convert("RGB")

            if len(output_images) == 0:
                w = image_data.size[0]
                h = image_data.size[1]

            if image_data.size[0] != w or image_data.size[1] != h:
                continue

            image_array = np.array(image_data).astype(np.float32) / 255.0
            image_tensor = torch.from_numpy(image_array)[None,]
            if "A" in i.getbands():
                mask = np.array(i.getchannel("A")).astype(np.float32) / 255.0
                mask = 1.0 - torch.from_numpy(mask)
            elif i.mode == "P" and "transparency" in i.info:
                mask = np.array(i.convert("RGBA").getchannel("A")).astype(np.float32) / 255.0
                mask = 1.0 - torch.from_numpy(mask)
            else:
                mask = torch.zeros((64, 64), dtype=torch.float32, device="cpu")
            output_images.append(image_tensor)
            output_masks.append(mask.unsqueeze(0))

            if img.format == "MPO":
                break  # ignore all frames except the first one for MPO format

        if len(output_images) > 1:
            output_image = torch.cat(output_images, dim=0)
            output_mask = torch.cat(output_masks, dim=0)
        else:
            output_image = output_images[0]
            output_mask = output_masks[0]

        # Load metadata
        metadata = self.load_metadata(image)

        return (
            output_image,
            output_mask,
            metadata["clip_skip"],
            metadata["positive"],
            metadata["negative"],
            metadata["seed"],
            metadata["width"],
            metadata["height"],
            metadata["steps"],
            metadata["cfg"],
        )

    @classmethod
    def IS_CHANGED(s, image):
        image_path = folder_paths.get_annotated_filepath(image)
        m = hashlib.sha256()
        with open(image_path, "rb") as f:
            m.update(f.read())

        # Also check if meta.json has changed
        input_dir = folder_paths.get_input_directory()
        meta_path = os.path.join(input_dir, "meta.json")
        if os.path.exists(meta_path):
            with open(meta_path, "rb") as f:
                m.update(f.read())

        return m.digest().hex()

    @classmethod
    def VALIDATE_INPUTS(s, image):
        if not folder_paths.exists_annotated_filepath(image):
            return "Invalid image file: {}".format(image)

        return True
