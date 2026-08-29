"""
bong_tangent scheduler - ported core math from RES4LYF (ClownsharkBatwing).

Source reference (confirmed via public mirror):
https://github.com/ClownsharkBatwing/RES4LYF/blob/a3999a56a650da5cffe9e8f9f8b115f764603620/sigmas.py#L4065

RES4LYF is licensed under AGPL-3.0 with an additional commercial-use rider.
If this file is distributed, keep this attribution header and confirm your
own distribution complies with AGPL-3.0 (and the commercial rider if
applicable to your use case).

NOTE ON FIDELITY:
The two functions below (`get_bong_tangent_sigmas` and `bong_tangent_scheduler`)
are a faithful port of the confirmed public source (verified against a
third-party mirror of sigmas.py, since the blob was too large to diff
line-by-line here). The `bong_tangent_scheduler_for_model` wrapper at the
bottom, which adapts this into a ComfyUI-style (model_sampling, steps) ->
SIGMAS pipeline, is NOT copied from RES4LYF (its exact internal glue code
between the normalized shape and the model's real sigma range was not
directly inspected) - it is a reconstruction following the same convention
ComfyUI's own custom schedulers (karras/exponential) use. Treat it as a
reasonable first pass, and A/B it against the real RES4LYF node before
relying on it for production work.
"""

import numpy as np
import torch


def get_bong_tangent_sigmas(steps, slope, pivot, start, end):
    """Single-stage tangent-shaped interpolation from `start` to `end`."""
    smax = ((2 / np.pi) * np.arctan(-slope * (0 - pivot)) + 1) / 2
    smin = ((2 / np.pi) * np.arctan(-slope * ((steps - 1) - pivot)) + 1) / 2

    srange = smax - smin
    sscale = start - end

    sigmas = [
        (((2 / np.pi) * np.arctan(-slope * (x - pivot)) + 1) / 2 - smin) * (1 / srange) * sscale + end
        for x in range(steps)
    ]
    return sigmas


def bong_tangent_scheduler(
    steps,
    start=1.0,
    middle=0.5,
    end=0.0,
    pivot_1=0.6,
    pivot_2=0.6,
    slope_1=0.2,
    slope_2=0.2,
    pad=False,
):
    """Two-stage tangent schedule: start -> middle -> end.

    Stage 1 uses (slope_1, pivot_1) to go from `start` to `middle`.
    Stage 2 uses (slope_2, pivot_2) to go from `middle` to `end`.
    """
    steps += 2

    midpoint = int((steps * pivot_1 + steps * pivot_2) / 2)
    pivot_1_i = int(steps * pivot_1)
    pivot_2_i = int(steps * pivot_2)

    slope_1 = slope_1 / (steps / 40)
    slope_2 = slope_2 / (steps / 40)

    stage_2_len = steps - midpoint
    stage_1_len = steps - stage_2_len

    tan_sigmas_1 = get_bong_tangent_sigmas(stage_1_len, slope_1, pivot_1_i, start, middle)
    tan_sigmas_2 = get_bong_tangent_sigmas(stage_2_len, slope_2, pivot_2_i - stage_1_len, middle, end)

    tan_sigmas_1 = tan_sigmas_1[:-1]
    if pad:
        tan_sigmas_2 = tan_sigmas_2 + [0]

    tan_sigmas = tan_sigmas_1 + tan_sigmas_2
    return tan_sigmas


def bong_tangent_scheduler_for_model(
    model_sampling,
    steps,
    pivot_1=0.6,
    pivot_2=0.6,
    slope_1=0.2,
    slope_2=0.2,
):
    """Adapts bong_tangent_scheduler() to ComfyUI's (model_sampling, steps) -> SIGMAS convention.

    This part is a reconstruction, not a verbatim RES4LYF snippet - see the
    module docstring. It substitutes the model's real sigma_max/sigma_min
    for the normalized start=1.0/end=0.0 used in the reference plot code,
    and appends a terminal 0.0 the way ComfyUI's own schedulers do.
    """
    sigma_max = float(model_sampling.sigma_max)
    sigma_min = float(model_sampling.sigma_min)

    # bong_tangent_scheduler(N, ...) returns N+1 values ending at `end`.
    # We want the final tensor to have `steps + 1` values total, with the
    # very last one being an exact 0.0 (ComfyUI convention) rather than
    # sigma_min - so we generate `steps` values ending at sigma_min, then
    # append the terminal 0.0 ourselves.
    sigmas = bong_tangent_scheduler(
        steps - 1,
        start=sigma_max,
        middle=(sigma_max + sigma_min) / 2,
        end=sigma_min,
        pivot_1=pivot_1,
        pivot_2=pivot_2,
        slope_1=slope_1,
        slope_2=slope_2,
        pad=False,
    )
    sigmas = list(sigmas) + [0.0]
    return torch.FloatTensor(sigmas)
