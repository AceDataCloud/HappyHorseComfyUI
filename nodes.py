"""ComfyUI Happy Horse graph nodes with native VIDEO output."""

from __future__ import annotations

import json
from io import BytesIO

from .client import (ACTION_MODELS, RATIOS, RESOLUTIONS, HappyHorseError,
                     download_video, retrieve, retrieve_batch, submit)


def _submitted(result):
    status, task_id, video_url, trace_id = result
    return {"ui": {"text": [f"Happy Horse status: {status}",
                            f"Task ID: {task_id or 'completed synchronously'}",
                            "Use Retrieve with this ID; do not resubmit to poll." if task_id and not video_url
                            else "Video is ready."]},
            "result": (status, task_id, video_url, trace_id)}



class _FreshTaskLookup:
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Task state changes remotely even when this graph's inputs do not.
        return float('nan')

class AceHappyHorseTextToVideo:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "prompt": ("STRING", {"multiline": True, "default": "A white horse runs across a moonlit beach."}),
            "model": (list(ACTION_MODELS["generate"]), {"default": "happyhorse-1.1-t2v"}),
            "resolution": (list(RESOLUTIONS), {"default": "720P"}),
            "ratio": (list(RATIOS), {"default": "16:9"}),
            "duration": ("INT", {"default": 5, "min": 3, "max": 15}),
            "watermark": ("BOOLEAN", {"default": False}),
            "seed": ("INT", {"default": -1, "min": -1, "max": 2147483647}),
        }}

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("status", "task_id", "video_url", "trace_id")
    FUNCTION = "run"
    CATEGORY = "Ace Data Cloud/Happy Horse"
    DESCRIPTION = "Submit one paid Happy Horse text-to-video task. Retrieve the returned task ID."
    OUTPUT_NODE = True

    def run(self, prompt, model, resolution, ratio, duration, watermark, seed):
        return _submitted(submit("generate", model, prompt, resolution=resolution, ratio=ratio,
                                 duration=duration, watermark=watermark, seed=seed))


class AceHappyHorseImageToVideo:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "image_url": ("STRING", {"default": ""}),
            "prompt": ("STRING", {"multiline": True, "default": "The scene gently comes to life."}),
            "model": (list(ACTION_MODELS["image_to_video"]), {"default": "happyhorse-1.1-i2v"}),
            "resolution": (list(RESOLUTIONS), {"default": "720P"}),
            "duration": ("INT", {"default": 5, "min": 3, "max": 15}),
            "watermark": ("BOOLEAN", {"default": False}),
            "seed": ("INT", {"default": -1, "min": -1, "max": 2147483647}),
        }}

    RETURN_TYPES = AceHappyHorseTextToVideo.RETURN_TYPES
    RETURN_NAMES = AceHappyHorseTextToVideo.RETURN_NAMES
    FUNCTION = "run"
    CATEGORY = AceHappyHorseTextToVideo.CATEGORY
    DESCRIPTION = "Animate a public HTTPS first-frame image. The image controls output ratio."
    OUTPUT_NODE = True

    def run(self, image_url, prompt, model, resolution, duration, watermark, seed):
        return _submitted(submit("image_to_video", model, prompt, image_url=image_url,
                                 resolution=resolution, duration=duration, watermark=watermark, seed=seed))


class AceHappyHorseReferenceToVideo:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "prompt": ("STRING", {"multiline": True, "default": "Keep this character consistent across the shot."}),
            "reference_image_urls": ("STRING", {"multiline": True, "default": ""}),
            "model": (list(ACTION_MODELS["reference_to_video"]), {"default": "happyhorse-1.1-r2v"}),
            "resolution": (list(RESOLUTIONS), {"default": "720P"}),
            "ratio": (list(RATIOS), {"default": "16:9"}),
            "duration": ("INT", {"default": 5, "min": 3, "max": 15}),
            "watermark": ("BOOLEAN", {"default": False}),
            "seed": ("INT", {"default": -1, "min": -1, "max": 2147483647}),
        }}

    RETURN_TYPES = AceHappyHorseTextToVideo.RETURN_TYPES
    RETURN_NAMES = AceHappyHorseTextToVideo.RETURN_NAMES
    FUNCTION = "run"
    CATEGORY = AceHappyHorseTextToVideo.CATEGORY
    DESCRIPTION = "Submit 1–9 public HTTPS reference images for video generation."
    OUTPUT_NODE = True

    def run(self, prompt, reference_image_urls, model, resolution, ratio, duration, watermark, seed):
        return _submitted(submit("reference_to_video", model, prompt, image_urls=reference_image_urls,
                                 resolution=resolution, ratio=ratio, duration=duration,
                                 watermark=watermark, seed=seed))


class AceHappyHorseVideoEdit:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "prompt": ("STRING", {"multiline": True, "default": "Replace the background with a sunny meadow."}),
            "video_url": ("STRING", {"default": ""}),
            "reference_image_urls": ("STRING", {"multiline": True, "default": ""}),
            "model": (list(ACTION_MODELS["video_edit"]),),
            "resolution": (list(RESOLUTIONS), {"default": "720P"}),
            "audio_setting": (["auto", "origin"], {"default": "auto"}),
            "watermark": ("BOOLEAN", {"default": False}),
            "seed": ("INT", {"default": -1, "min": -1, "max": 2147483647}),
        }}

    RETURN_TYPES = AceHappyHorseTextToVideo.RETURN_TYPES
    RETURN_NAMES = AceHappyHorseTextToVideo.RETURN_NAMES
    FUNCTION = "run"
    CATEGORY = AceHappyHorseTextToVideo.CATEGORY
    DESCRIPTION = "Edit a public HTTPS video with up to five optional reference images."
    OUTPUT_NODE = True

    def run(self, prompt, video_url, reference_image_urls, model, resolution, audio_setting, watermark, seed):
        return _submitted(submit("video_edit", model, prompt, video_url=video_url,
                                 image_urls=reference_image_urls, resolution=resolution,
                                 audio_setting=audio_setting, watermark=watermark, seed=seed))


class AceHappyHorseRetrieve(_FreshTaskLookup):
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "task_id": ("STRING", {"default": ""}),
            "wait_seconds": ("INT", {"default": 240, "min": 0, "max": 240, "step": 5}),
        }}

    RETURN_TYPES = AceHappyHorseTextToVideo.RETURN_TYPES
    RETURN_NAMES = AceHappyHorseTextToVideo.RETURN_NAMES
    FUNCTION = "run"
    CATEGORY = AceHappyHorseTextToVideo.CATEGORY
    DESCRIPTION = "Read an existing task; connect video_url to Load Video after success."
    OUTPUT_NODE = True

    def run(self, task_id: str, wait_seconds: int):
        status, task_id, video_url, trace_id = retrieve(task_id, wait_seconds)
        return {"ui": {"text": [f"Happy Horse status: {status}", f"Task ID: {task_id}",
                                "Video is ready" if video_url else "Query this ID again later"]},
                "result": (status, task_id, video_url, trace_id)}


class AceHappyHorseRetrieveBatch(_FreshTaskLookup):
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"task_ids_json": ("STRING", {"multiline": True, "default": "[]"})}}

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("results_json",)
    FUNCTION = "run"
    CATEGORY = AceHappyHorseTextToVideo.CATEGORY
    DESCRIPTION = "Read 1–20 existing task IDs without creating video tasks."
    OUTPUT_NODE = True

    def run(self, task_ids_json: str):
        rows = retrieve_batch(task_ids_json)
        return {"ui": {"text": [f"Retrieved {len(rows)} Happy Horse tasks"]},
                "result": (json.dumps(rows),)}


class AceHappyHorseLoadVideo:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"video_url": ("STRING", {"default": ""})}}

    RETURN_TYPES = ("VIDEO",)
    RETURN_NAMES = ("video",)
    FUNCTION = "run"
    CATEGORY = AceHappyHorseTextToVideo.CATEGORY
    DESCRIPTION = "Load an Ace Data Cloud video link as native ComfyUI VIDEO."

    def run(self, video_url: str):
        if not video_url:
            raise HappyHorseError("Task is still pending. Retrieve the same task ID again.")
        from comfy_api.latest import VideoFromFile

        return (VideoFromFile(BytesIO(download_video(video_url))),)
