"""
Figure Generation for All Equations
Creates clean, academic-style conceptual diagrams for each regression specification.
No overlapping elements, proper spacing, Times New Roman typography.
"""

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch, FancyBboxPatch
from matplotlib.patches import Circle
import numpy as np
from loguru import logger

# Academic thesis style
TNR = "Times New Roman"
plt.rcParams["font.family"] = "serif"
plt.rcParams["font.serif"] = [TNR] + plt.rcParams["font.serif"]

# Color scheme (muted, professional)
COLOR_ROBOT = "#2E5090"      # Dark blue
COLOR_EMPLOY = "#8B0000"     # Dark red
COLOR_INST = "#2F4F4F"       # Dark slate gray
COLOR_ARROW = "#000000"      # Black
COLOR_MOD_ARROW = "#696969"  # Dim gray


# =============================================================================
# FIGURE 1: BASELINE MODEL (Equation 1)
# =============================================================================
def make_figure1_baseline(out_path="outputs/figure1_baseline.png"):
    """
    Equation 1: ln(Hours) ~ ln(Robots) + controls + FE
    Simple main effect, no moderation
    """
    fig, ax = plt.subplots(figsize=(10, 4), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4)
    ax.axis("off")
    
    # Title
    ax.text(5, 3.7, "Figure 1: Baseline Model (Equation 1)", 
            ha="center", va="top", fontsize=14, weight="bold")
    ax.text(5, 3.4, "Main effect: Do robots affect employment?", 
            ha="center", va="top", fontsize=11, style="italic")
    
    # Boxes
    def add_box(x, y, w, h, text, color, fontsize=11):
        box = FancyBboxPatch(
            (x - w/2, y - h/2), w, h,
            boxstyle="round,pad=0.1",
            linewidth=2,
            facecolor="white",
            edgecolor=color
        )
        ax.add_patch(box)
        ax.text(x, y, text, ha="center", va="center", 
                fontsize=fontsize, weight="bold", color=color)
    
    # Robot box (left)
    add_box(2, 2, 2.5, 1.2, "Robot Stock\n(IFR)", COLOR_ROBOT, 12)
    
    # Employment box (right)
    add_box(8, 2, 2.5, 1.2, "Hours Worked\n(EU KLEMS)", COLOR_EMPLOY, 12)
    
    # Arrow
    arrow = FancyArrowPatch(
        (3.25, 2), (6.75, 2),
        arrowstyle="-|>",
        mutation_scale=25,
        linewidth=3,
        color=COLOR_ARROW
    )
    ax.add_patch(arrow)
    
    # Arrow label
    ax.text(5, 2.5, "β₁ = ?", ha="center", va="bottom", 
            fontsize=13, weight="bold", style="italic")
    
    # Control variables note
    ax.text(5, 0.7, "Controls: Value added, Capital, GDP, Unemployment", 
            ha="center", va="top", fontsize=9, style="italic", color="gray")
    ax.text(5, 0.4, "Fixed Effects: Country-Industry, Year", 
            ha="center", va="top", fontsize=9, style="italic", color="gray")
    
    plt.tight_layout()
    fig.savefig(out_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out_path


# =============================================================================
# FIGURE 2: COORDINATION MODERATION (Equation 2)
# =============================================================================
def make_figure2_coordination(out_path="outputs/figure2_coordination_moderation.png"):
    """
    Equation 2: ln(Hours) ~ ln(Robots) × High_Coord + controls + FE
    Moderation by coordination
    """
    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis("off")
    
    # Title
    ax.text(5, 4.7, "Figure 2: Coordination Moderation (Equation 2)", 
            ha="center", va="top", fontsize=14, weight="bold")
    ax.text(5, 4.4, "Does coordination buffer robot displacement?", 
            ha="center", va="top", fontsize=11, style="italic")
    
    # Boxes
    def add_box(x, y, w, h, text, color, fontsize=11):
        box = FancyBboxPatch(
            (x - w/2, y - h/2), w, h,
            boxstyle="round,pad=0.1",
            linewidth=2,
            facecolor="white",
            edgecolor=color
        )
        ax.add_patch(box)
        ax.text(x, y, text, ha="center", va="center", 
                fontsize=fontsize, weight="bold", color=color)
    
    # Robot (left)
    add_box(2, 2.5, 2.5, 1.2, "Robot Stock\n(IFR)", COLOR_ROBOT, 12)
    
    # Employment (right)
    add_box(8, 2.5, 2.5, 1.2, "Hours Worked\n(EU KLEMS)", COLOR_EMPLOY, 12)
    
    # Coordination (bottom)
    add_box(5, 0.8, 3.5, 1, "Collective Bargaining\nCoordination (ICTWSS)", 
            COLOR_INST, 11)
    
    # Main effect arrow
    arrow_main = FancyArrowPatch(
        (3.25, 2.5), (6.75, 2.5),
        arrowstyle="-|>",
        mutation_scale=25,
        linewidth=3,
        color=COLOR_ARROW
    )
    ax.add_patch(arrow_main)
    ax.text(5, 3.1, "β₁ (baseline)", ha="center", va="bottom", 
            fontsize=11, weight="bold")
    
    # Moderation arrow (dashed)
    arrow_mod = FancyArrowPatch(
        (5, 1.3), (5, 1.9),
        arrowstyle="-|>",
        mutation_scale=20,
        linewidth=2.5,
        linestyle="--",
        color=COLOR_MOD_ARROW
    )
    ax.add_patch(arrow_mod)
    ax.text(5.8, 1.6, "β₂ (moderation)", ha="left", va="center", 
            fontsize=11, weight="bold", color=COLOR_MOD_ARROW)
    
    # Interpretation box
    ax.text(5, 0.2, 
            "β₂ > 0: Coordination buffers displacement  |  β₂ < 0: Coordination amplifies harm", 
            ha="center", va="top", fontsize=9, style="italic",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="lightyellow", alpha=0.7))
    
    plt.tight_layout()
    fig.savefig(out_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out_path


# =============================================================================
# FIGURE 3: COVERAGE MODERATION (Equation 3)
# =============================================================================
def make_figure3_coverage(out_path="outputs/figure3_coverage_moderation.png"):
    """
    Equation 3: ln(Hours) ~ ln(Robots) × Coverage + controls + FE
    Moderation by coverage (continuous)
    """
    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis("off")
    
    # Title
    ax.text(5, 4.7, "Figure 3: Coverage Moderation (Equation 3)", 
            ha="center", va="top", fontsize=14, weight="bold")
    ax.text(5, 4.4, "Does bargaining coverage moderate robot effects?", 
            ha="center", va="top", fontsize=11, style="italic")
    
    # Boxes
    def add_box(x, y, w, h, text, color, fontsize=11):
        box = FancyBboxPatch(
            (x - w/2, y - h/2), w, h,
            boxstyle="round,pad=0.1",
            linewidth=2,
            facecolor="white",
            edgecolor=color
        )
        ax.add_patch(box)
        ax.text(x, y, text, ha="center", va="center", 
                fontsize=fontsize, weight="bold", color=color)
    
    # Robot (left)
    add_box(2, 2.5, 2.5, 1.2, "Robot Stock\n(IFR)", COLOR_ROBOT, 12)
    
    # Employment (right)
    add_box(8, 2.5, 2.5, 1.2, "Hours Worked\n(EU KLEMS)", COLOR_EMPLOY, 12)
    
    # Coverage (bottom)
    add_box(5, 0.8, 3.5, 1, "Bargaining Coverage\nAdjCov (ICTWSS)", 
            COLOR_INST, 11)
    
    # Main effect arrow
    arrow_main = FancyArrowPatch(
        (3.25, 2.5), (6.75, 2.5),
        arrowstyle="-|>",
        mutation_scale=25,
        linewidth=3,
        color=COLOR_ARROW
    )
    ax.add_patch(arrow_main)
    ax.text(5, 3.1, "β₁ (at mean coverage)", ha="center", va="bottom", 
            fontsize=11, weight="bold")
    
    # Moderation arrow (dashed)
    arrow_mod = FancyArrowPatch(
        (5, 1.3), (5, 1.9),
        arrowstyle="-|>",
        mutation_scale=20,
        linewidth=2.5,
        linestyle="--",
        color=COLOR_MOD_ARROW
    )
    ax.add_patch(arrow_mod)
    ax.text(5.8, 1.6, "β₂ (per 1pp coverage)", ha="left", va="center", 
            fontsize=11, weight="bold", color=COLOR_MOD_ARROW)
    
    # Interpretation box
    ax.text(5, 0.2, 
            "Note: Sample restricted to 11 Western European countries (missing data for 6 Eastern European countries)", 
            ha="center", va="top", fontsize=8, style="italic", color="red",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="mistyrose", alpha=0.7))
    
    plt.tight_layout()
    fig.savefig(out_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out_path


# =============================================================================
# FIGURE 4: INDUSTRY HETEROGENEITY - COORDINATION (Equation 4)
# =============================================================================
def make_figure4_industry_coord(out_path="outputs/figure4_industry_coordination.png"):
    """
    Equation 4: Run Equation 2 separately for each industry
    Shows 13 separate regressions
    """
    fig, ax = plt.subplots(figsize=(12, 6), dpi=300)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6)
    ax.axis("off")
    
    # Title
    ax.text(6, 5.7, "Figure 4: Industry-by-Industry Coordination Effects (Equation 4)", 
            ha="center", va="top", fontsize=14, weight="bold")
    ax.text(6, 5.4, "Does coordination work differently across industries?", 
            ha="center", va="top", fontsize=11, style="italic")
    
    # Show grid of mini-models (3x5 grid for 13 industries)
    industries = [
        ("C21\nPharma", "+4.9%***"),
        ("C19\nPetrol", "+13.9%*"),
        ("C20-21\nChem", "+2.8%***"),
        ("C31-33\nFurn", "+9.6%***"),
        ("C16-18\nWood", "+1.9%"),
        ("C26-27\nElec", "+1.3%"),
        ("C22-23\nPlast", "+1.7%"),
        ("C29-30\nAuto", "-2.4%"),
        ("C\nTotal", "+1.2%"),
        ("C24-25\nMetal", "-0.8%"),
        ("C13-15\nText", "-0.7%"),
        ("C10-12\nFood", "-0.5%"),
        ("C28\nMach", "-7.1%*")
    ]
    
    # Grid layout
    rows, cols = 3, 5
    x_start, y_start = 0.5, 4.5
    x_gap, y_gap = 2.3, 1.3
    
    for idx, (ind_name, effect) in enumerate(industries):
        row = idx // cols
        col = idx % cols
        
        x = x_start + col * x_gap
        y = y_start - row * y_gap
        
        # Small box for each industry
        box_w, box_h = 2, 0.8
        
        # Color based on significance and direction
        if "***" in effect or "**" in effect or "*" in effect:
            if "+" in effect:
                color = "#90EE90"  # Light green (positive & significant)
            else:
                color = "#FFB6C1"  # Light red (negative & significant)
        else:
            color = "#D3D3D3"  # Light gray (not significant)
        
        box = Rectangle(
            (x - box_w/2, y - box_h/2), box_w, box_h,
            linewidth=1.5,
            facecolor=color,
            edgecolor="black"
        )
        ax.add_patch(box)
        
        # Industry name
        ax.text(x, y + 0.15, ind_name, ha="center", va="center", 
                fontsize=8, weight="bold")
        
        # Effect size
        ax.text(x, y - 0.15, effect, ha="center", va="center", 
                fontsize=9, weight="bold", style="italic")
    
    # Legend
    legend_y = 0.6
    ax.text(1.5, legend_y, "■", fontsize=20, color="#90EE90", ha="center")
    ax.text(2.3, legend_y, "Positive & Significant", fontsize=9, ha="left", va="center")
    
    ax.text(5, legend_y, "■", fontsize=20, color="#FFB6C1", ha="center")
    ax.text(5.8, legend_y, "Negative & Significant", fontsize=9, ha="left", va="center")
    
    ax.text(8.5, legend_y, "■", fontsize=20, color="#D3D3D3", ha="center")
    ax.text(9.3, legend_y, "Not Significant", fontsize=9, ha="left", va="center")
    
    # Note
    ax.text(6, 0.2, 
            "Each box = separate regression for one industry. Shows coordination moderation effect (β₂).", 
            ha="center", va="top", fontsize=8, style="italic",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="lightyellow", alpha=0.7))
    
    plt.tight_layout()
    fig.savefig(out_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out_path


# =============================================================================
# FIGURE 5: INDUSTRY HETEROGENEITY - COVERAGE (Equation 5)
# =============================================================================
def make_figure5_industry_coverage(out_path="outputs/figure5_industry_coverage.png"):
    """
    Equation 5: Run Equation 3 separately for each industry
    Shows 13 separate regressions
    """
    fig, ax = plt.subplots(figsize=(12, 6), dpi=300)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6)
    ax.axis("off")
    
    # Title
    ax.text(6, 5.7, "Figure 5: Industry-by-Industry Coverage Effects (Equation 5)", 
            ha="center", va="top", fontsize=14, weight="bold")
    ax.text(6, 5.4, "Does coverage moderate robot effects differently across industries?", 
            ha="center", va="top", fontsize=11, style="italic")
    
    # Show grid of mini-models
    industries = [
        ("C16-18\nWood", "+0.29%***"),
        ("C21\nPharma", "+0.14%"),
        ("C28\nMach", "+0.27%"),
        ("C20-21\nChem", "+0.02%"),
        ("C22-23\nPlast", "+0.06%"),
        ("C19\nPetrol", "-0.11%"),
        ("C\nTotal", "-0.11%"),
        ("C10-12\nFood", "-0.10%"),
        ("C26-27\nElec", "-0.22%***"),
        ("C31-33\nFurn", "-0.29%"),
        ("C13-15\nText", "-0.36%*"),
        ("C29-30\nAuto", "-0.38%**"),
        ("C24-25\nMetal", "-0.39%***")
    ]
    
    # Grid layout
    rows, cols = 3, 5
    x_start, y_start = 0.5, 4.5
    x_gap, y_gap = 2.3, 1.3
    
    for idx, (ind_name, effect) in enumerate(industries):
        row = idx // cols
        col = idx % cols
        
        x = x_start + col * x_gap
        y = y_start - row * y_gap
        
        # Small box for each industry
        box_w, box_h = 2, 0.8
        
        # Color based on significance and direction
        if "***" in effect or "**" in effect or "*" in effect:
            if "+" in effect:
                color = "#90EE90"  # Light green (positive & significant)
            else:
                color = "#FFB6C1"  # Light red (negative & significant)
        else:
            color = "#D3D3D3"  # Light gray (not significant)
        
        box = Rectangle(
            (x - box_w/2, y - box_h/2), box_w, box_h,
            linewidth=1.5,
            facecolor=color,
            edgecolor="black"
        )
        ax.add_patch(box)
        
        # Industry name
        ax.text(x, y + 0.15, ind_name, ha="center", va="center", 
                fontsize=8, weight="bold")
        
        # Effect size
        ax.text(x, y - 0.15, effect, ha="center", va="center", 
                fontsize=9, weight="bold", style="italic")
    
    # Legend
    legend_y = 0.6
    ax.text(1.5, legend_y, "■", fontsize=20, color="#90EE90", ha="center")
    ax.text(2.3, legend_y, "Positive & Significant", fontsize=9, ha="left", va="center")
    
    ax.text(5, legend_y, "■", fontsize=20, color="#FFB6C1", ha="center")
    ax.text(5.8, legend_y, "Negative & Significant", fontsize=9, ha="left", va="center")
    
    ax.text(8.5, legend_y, "■", fontsize=20, color="#D3D3D3", ha="center")
    ax.text(9.3, legend_y, "Not Significant", fontsize=9, ha="left", va="center")
    
    # Note
    ax.text(6, 0.2, 
            "Each box = separate regression. Shows coverage moderation effect (β₂: change per 1pp coverage increase).", 
            ha="center", va="top", fontsize=8, style="italic",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="mistyrose", alpha=0.7))
    
    plt.tight_layout()
    fig.savefig(out_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out_path


# =============================================================================
# MAIN: Generate All Figures
# =============================================================================
if __name__ == "__main__":
    logger.info("Generating conceptual figures for all equations...")
    
    fig1 = make_figure1_baseline()
    logger.info(f"✓ Created: {fig1}")
    
    fig2 = make_figure2_coordination()
    logger.info(f"✓ Created: {fig2}")
    
    fig3 = make_figure3_coverage()
    logger.info(f"✓ Created: {fig3}")
    
    fig4 = make_figure4_industry_coord()
    logger.info(f"✓ Created: {fig4}")
    
    fig5 = make_figure5_industry_coverage()
    logger.info(f"✓ Created: {fig5}")
    
    logger.info("\n✓ All figures generated successfully!")