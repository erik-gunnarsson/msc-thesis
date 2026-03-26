from __future__ import annotations

from typing import Optional


BAR = "═" * 56
SEP = "─" * 56


MODERATOR_REGISTRY = {
    "coord": {
        "mod_var": "coord_pre_c",
        "continuous_var": "coord_pre",
        "centered_var": "coord_pre_c",
        "binary_var": "high_coord_pre",
        "has_var": "has_coord",
        "is_binary": False,
        "label": "Bargaining coordination",
        "role_label": "primary focal moderator",
        "workflow_tier": "primary",
        "active_workflow": True,
        "priority_rank": 1,
        "theory_note": "Bargaining coordination is the headline institutional channel because it combines strong theory fit with workable country coverage.",
        "sample_caveat": "Preferred focal specification in the active WIOD workflow.",
    },
    "adjcov": {
        "mod_var": "adjcov_pre_c",
        "continuous_var": "adjcov_pre",
        "centered_var": "adjcov_pre_c",
        "has_var": "has_adjcov",
        "is_binary": False,
        "label": "Adjusted collective-bargaining coverage",
        "role_label": "secondary focal moderator",
        "workflow_tier": "secondary",
        "active_workflow": True,
        "priority_rank": 2,
        "theory_note": "Adjusted collective-bargaining coverage is theoretically important, but inference is constrained by the smaller common-sample country set.",
        "sample_caveat": "Restricted/common-sample specification in practice.",
    },
    "ud": {
        "mod_var": "ud_pre_c",
        "continuous_var": "ud_pre",
        "centered_var": "ud_pre_c",
        "has_var": "has_ud",
        "is_binary": False,
        "label": "Union density",
        "role_label": "reference benchmark",
        "workflow_tier": "reference",
        "active_workflow": True,
        "priority_rank": 3,
        "theory_note": "Union density is retained as a reference comparison because it has broader coverage, but it is not a focal institutional channel in the thesis theory.",
        "sample_caveat": "Reference benchmark only; do not treat as co-equal with coord or adjcov.",
    },
}


MAINLINE_MODERATORS = ["coord", "adjcov", "ud"]


def ordered_moderator_keys(keys: Optional[list[str]] = None, *, active_only: bool = False) -> list[str]:
    key_list = list(keys or MODERATOR_REGISTRY.keys())
    if active_only:
        key_list = [key for key in key_list if MODERATOR_REGISTRY[key].get("active_workflow", False)]
    return sorted(
        key_list,
        key=lambda key: (
            MODERATOR_REGISTRY[key].get("priority_rank", 999),
            MODERATOR_REGISTRY[key].get("label", key),
        ),
    )


def get_moderator(mod_key: str = "coord") -> dict:
    if mod_key not in MODERATOR_REGISTRY:
        raise ValueError(f"Unknown moderator '{mod_key}'. Choose from: {list(MODERATOR_REGISTRY.keys())}")
    return MODERATOR_REGISTRY[mod_key]


def moderator_role_summary(mod_key: str) -> str:
    info = get_moderator(mod_key)
    return f"{info['role_label']} — {info['theory_note']}"
