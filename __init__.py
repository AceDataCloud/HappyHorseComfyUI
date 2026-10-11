"""Happy Horse nodes for ComfyUI."""

from .nodes import (AceHappyHorseImageToVideo, AceHappyHorseLoadVideo,
                    AceHappyHorseReferenceToVideo, AceHappyHorseRetrieve,
                    AceHappyHorseRetrieveBatch, AceHappyHorseTextToVideo,
                    AceHappyHorseVideoEdit)

NODE_CLASS_MAPPINGS = {
    "AceHappyHorseTextToVideo": AceHappyHorseTextToVideo,
    "AceHappyHorseImageToVideo": AceHappyHorseImageToVideo,
    "AceHappyHorseReferenceToVideo": AceHappyHorseReferenceToVideo,
    "AceHappyHorseVideoEdit": AceHappyHorseVideoEdit,
    "AceHappyHorseRetrieve": AceHappyHorseRetrieve,
    "AceHappyHorseRetrieveBatch": AceHappyHorseRetrieveBatch,
    "AceHappyHorseLoadVideo": AceHappyHorseLoadVideo,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "AceHappyHorseTextToVideo": "Happy Horse Text to Video (Ace Data Cloud)",
    "AceHappyHorseImageToVideo": "Happy Horse Image to Video (Ace Data Cloud)",
    "AceHappyHorseReferenceToVideo": "Happy Horse Reference to Video (Ace Data Cloud)",
    "AceHappyHorseVideoEdit": "Happy Horse Video Edit (Ace Data Cloud)",
    "AceHappyHorseRetrieve": "Happy Horse Retrieve Task (Ace Data Cloud)",
    "AceHappyHorseRetrieveBatch": "Happy Horse Retrieve Tasks (Ace Data Cloud)",
    "AceHappyHorseLoadVideo": "Happy Horse Load Video (Ace Data Cloud)",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
