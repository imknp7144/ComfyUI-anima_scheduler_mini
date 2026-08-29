"""
anima_scheduler_lite - registers `beta57` and `bong_tangent` schedulers
directly into ComfyUI's core scheduler list, the same way RES4LYF does,
so they show up in every standard KSampler-style scheduler dropdown
(instead of only being available as a separate SIGMAS-output node).

If RES4LYF is also installed and already registered these names, we skip
registration to avoid clobbering it - whichever loads first wins, and
since both are meant to be numerically equivalent for beta57 (and a
best-effort reconstruction for bong_tangent, see bong_tangent.py), this
should be harmless either way.
"""

from functools import partial

import comfy.samplers

from .bong_tangent import bong_tangent_scheduler_for_model
from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]


def _register_scheduler(name, handler, use_ms=True):
    if name in comfy.samplers.SCHEDULER_HANDLERS:
        print(f"[anima_scheduler_lite] '{name}' is already registered (likely by RES4LYF) - skipping.")
        return
    comfy.samplers.SCHEDULER_HANDLERS[name] = comfy.samplers.SchedulerHandler(handler=handler, use_ms=use_ms)
    if name not in comfy.samplers.SCHEDULER_NAMES:
        comfy.samplers.SCHEDULER_NAMES.append(name)
    print(f"[anima_scheduler_lite] registered '{name}' scheduler.")


try:
    # beta57 == comfy's own beta_scheduler with alpha=0.5, beta=0.7
    # (this is literally how RES4LYF itself defines it - no custom math needed)
    _register_scheduler(
        "beta57",
        partial(comfy.samplers.beta_scheduler, alpha=0.5, beta=0.7),
        use_ms=True,
    )

    # bong_tangent: ported/reconstructed math, see bong_tangent.py.
    # Uses default pivot/slope values (0.6, 0.6, 0.2, 0.2) since the core
    # dispatcher only calls handler(model_sampling, steps) - no extra
    # kwargs. Use the standalone `Bong Tangent Scheduler` node instead if
    # you want to tune pivot_1/pivot_2/slope_1/slope_2.
    _register_scheduler(
        "bong_tangent",
        bong_tangent_scheduler_for_model,
        use_ms=True,
    )
except Exception as e:  # pragma: no cover - defensive: never break ComfyUI startup
    print(f"[anima_scheduler_lite] failed to register core schedulers: {e}")
