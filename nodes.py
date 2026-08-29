import torch

import comfy.model_management

from .bong_tangent import bong_tangent_scheduler_for_model


class BongTangentScheduler:
    """Standalone SIGMAS node for the bong_tangent shape (RES4LYF-derived).

    Mirrors the input/output shape of ComfyUI's built-in BasicScheduler /
    KarrasScheduler nodes so it drops into a SamplerCustom(Advanced) chain
    the same way.
    """

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model": ("MODEL",),
                "steps": ("INT", {"default": 30, "min": 1, "max": 10000}),
                "pivot_1": ("FLOAT", {"default": 0.6, "min": 0.0, "max": 1.0, "step": 0.01}),
                "pivot_2": ("FLOAT", {"default": 0.6, "min": 0.0, "max": 1.0, "step": 0.01}),
                "slope_1": ("FLOAT", {"default": 0.2, "min": 0.01, "max": 5.0, "step": 0.01}),
                "slope_2": ("FLOAT", {"default": 0.2, "min": 0.01, "max": 5.0, "step": 0.01}),
                "denoise": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
            }
        }

    RETURN_TYPES = ("SIGMAS",)
    CATEGORY = "sampling/custom_sampling/schedulers"
    FUNCTION = "get_sigmas"

    def get_sigmas(self, model, steps, pivot_1, pivot_2, slope_1, slope_2, denoise):
        total_steps = steps
        if denoise < 1.0:
            if denoise <= 0.0:
                return (torch.FloatTensor([]),)
            total_steps = int(steps / denoise)

        comfy.model_management.load_models_gpu([model])
        model_sampling = model.get_model_object("model_sampling")

        sigmas = bong_tangent_scheduler_for_model(
            model_sampling,
            total_steps,
            pivot_1=pivot_1,
            pivot_2=pivot_2,
            slope_1=slope_1,
            slope_2=slope_2,
        )
        sigmas = sigmas[-(steps + 1):]
        return (sigmas,)


NODE_CLASS_MAPPINGS = {
    "BongTangentScheduler": BongTangentScheduler,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BongTangentScheduler": "Bong Tangent Scheduler (RES4LYF-derived)",
}
