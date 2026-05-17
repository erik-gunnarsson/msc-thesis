# Meeting questions — Rebecka, Friday 15 May 2026, 14:00–16:00

**Where:** B706, Saltmätargatan 13–17
**Who:** Erik (with Alice's hat on), Rebecka
**Why this slot matters:** This is Rebecka's **last methods-advice slot** before submission. Anything that needs her endorsement (inference policy, star convention, AdjCov keep/drop, Eq. 2b placement, headline phrasing) has to be locked here. After today I'm writing against whatever we agree, so I want methodological green lights, not exploration.

**What I want out of two hours:**
1. A single inference standard for the thesis-facing table (cluster-stars vs wild-stars vs no-stars + explicit p) and the language that goes with it.
2. A decision on AdjCov (Eq. 2 adjcov, 15 countries) and Eq. 2b Hawk–Dove placement.
3. A handful of small specification rulings (capital proxy, robot stock vs intensity, pre-crisis subsample, CH normalisation) so I stop re-litigating them in my head.
4. Submission-mile process: chapter order, page lengths, what she wants to see between today and the deadline.

I will run the meeting from the umbrella GitHub issue (created at the end of this doc); each numbered question below maps 1:1 to its own GitHub issue so I can take notes inside the issue while she talks. Background numbers below come from the 15 May snapshot in `results/_snapshot_20260515/`.

---

## Headline numbers I'm bringing into the meeting

From `results/_snapshot_20260515/core/wiod_first_results_overview.md` and `wiod_first_results_summary.csv`:

| Model | Sample (countries / entities / obs) | Focal term | Coef | SE | p (cluster) | p (wild) |
| --- | --- | --- | --- | --- | --- | --- |
| Eq. 1 baseline | 26 / 257 / 2571 | `ln_robots_lag1` | 0.0096 | 0.0062 | 0.119 | 0.126 |
| Eq. 2 coord (primary) | 25 / 247 / 2500 | `ln_robots_lag1:coord_pre_c` | **0.0124** | 0.0053 | **0.020** | **0.108** |
| Eq. 2 adjcov (restricted) | 15 / 153 / 1685 | `ln_robots_lag1:adjcov_pre_c` | 0.0003 | 0.0004 | 0.521 | 0.509 |
| Eq. 2 ud (reference) | 23 / 227 / 2356 | `ln_robots_lag1:ud_pre_c` | −0.00003 | 0.0004 | 0.939 | 0.955 |

Eq. 2b Hawk–Dove gate is `GO` (FE-style VIF max 1.38, all cells populated, see `results/_snapshot_20260515/wiod_eq2b_coord_ud_gate.md`) but the three-way `coord × ud × robots` term is far from significant (`p_wild ≈ 0.59`, see `results/_snapshot_20260515/secondary/wiod_eq2b_coord_ud_comparison.md`).

Sample vs specification decomposition (from `wiod_eq2_coord_sample_decomposition.md`):
- Eq. 2 coord, full 25-country sample: **0.0124** (p_wild 0.108)
- Eq. 2 coord, restricted to 23-country Eq. 2b intersection: **0.0142** (p_wild 0.101)
- Eq. 2b coord-slope term on same 23 countries: **0.0117** (p_wild 0.472)

→ moving to the smaller sample makes the coord interaction *larger*; the attenuation in Eq. 2b is **specification-driven** (adding `ud × robots` and the three-way absorbs shared variance), not sample-driven.

Common-sample robustness (`wiod_common_sample_robustness.md`, 23-country intersection): Eq. 2 coord interaction = 0.0142, p_wild = **0.068**; Eq. 2b three-way = −0.00041, p_wild = 0.591.

---

## Prioritised question list

### P0 — must-ask (inference + table policy + headline framing + appendix calls)

#### Q1. Cluster-vs-wild gap: how do I report 0.020 vs 0.108, and what star policy goes on the thesis-facing table?
- **Numbers:** Eq. 2 coord interaction `+0.0124`, `p_cluster = 0.020`, `p_wild = 0.108`, 999 reps.
- **Issues:** #9 (table policy), #4 (bootstrap audit).
- **Why I'm asking:** This is the single biggest interpretive question in the thesis. I have three live options: (A) cluster-clustered stars with wild p in notes (`wiod_regression_table_combined_clusterstars.md`), (B) wild-bootstrap stars with cluster SE in parentheses (`wiod_regression_table_combined.md`), (C) no stars + explicit p for both methods. I need her to pick one so the prose, the table notes, and the appendix all line up.

#### Q2. Acceptable headline language given `p_wild = 0.108`
- **Numbers:** see Q1.
- **Issues:** #4, #10.
- **Why I'm asking:** I want her exact phrasing for the §6.1.3 lede sentence. My current candidates range from "significant at the 5% level under country-clustered inference; suggestive under wild cluster bootstrap" to "weakly supports the coordination hypothesis"; I want to make sure I land on something she's comfortable defending in the seminar.

#### Q3. Few-cluster corrections beyond Rademacher wild — Mammen weights / CR2?
- **Numbers:** 25 country clusters for Eq. 2 coord; 23 for Eq. 2 ud / Eq. 2b; 15 for AdjCov.
- **Issues:** #4.
- **Why I'm asking:** If there's leftover time I'd like to add a second few-cluster correction column to the appendix (Mammen weights variant of the wild bootstrap, or CR2 bias-corrected cluster SE) to bracket the inference uncertainty. I want to know if she'd find that valuable or distracting, and whether she has a default preference.

#### Q4. AdjCov (15 countries) — keep as restricted secondary focal or demote to footnote?
- **Numbers:** Eq. 2 adjcov interaction = 0.0003, p_cluster = 0.52, p_wild = 0.51, 15 countries.
- **Issues:** #15.
- **Why I'm asking:** Current code keeps AdjCov as "secondary focal restricted-sample"; the draft §4.3.3 has an open "Remove ADJCOV completely?" note. I'd prefer to keep it as the restricted-sample reference and call out the cluster count as a limitation, but I want her ruling before I write that into §6.1.4.

#### Q5. Eq. 2b Hawk–Dove placement — appendix vs short §6.1.5 vs out
- **Numbers:** Gate `GO`; coord-slope `+0.0117`, p_wild = 0.47; three-way `−0.00041`, p_wild = 0.59; UD slope ≈ 0, p_wild = 0.99.
- **Issues:** #11.
- **Why I'm asking:** My current preference is a short §6.1.5 robustness subsection framed as null-evidence-on-UD (i.e. "coordination, not union density, is the active moderator"), with the regression in the appendix. The alternative is appendix-only or dropping it entirely. I want her green light before I commit to that framing, because it changes the architecture of §6.

#### Q6. Narrative framing — null Eq. 1 paired with positive Eq. 2 coord interaction
- **Numbers:** Eq. 1 `ln_robots_lag1` coef = 0.0096, p_cluster = 0.12; Eq. 2 coord interaction = +0.0124, p_cluster = 0.020.
- **Issues:** #10, #12.
- **Why I'm asking:** The cleanest H1/H2/H3 story I have is "no average effect; the institutional moderator is where the action is", which lines up with Leibrecht et al. (2023). I want to make sure she's comfortable with leading on the interaction rather than the baseline, and that "near-zero baseline is expected" is the right framing.

### P1 — high-priority (sample, specification, prose drift)

#### Q7. Switzerland exclusion + robot-stock vs robot-intensity as the headline regressor
- **Numbers:** CH excluded because IFR `robot_wrkr_stock_95` denominator is zero across CH sub-industries; current headline regressor is `ln_robots_lag1` (per-worker intensity).
- **Issues:** #20, #21.
- **Why I'm asking:** Two related sub-questions on the right-hand-side construction. (1) Should I defend the CH exclusion in the limitations section and document the alt-normalisation as a planned but infeasible robustness, or push to deliver a CH-inclusive sensitivity using a different denominator? (2) Does the field have a default she'd point me to (intensity vs log stock)? My priors are: keep intensity as headline (matches Leibrecht et al. 2023) and report `ln_robot_stock_lag1` as a robustness column. I want her to confirm.

#### Q8. Capital proxy K vs CAP, and the 2008–2009 exclusion column
- **Numbers:** Default is `K` (WIOD SEA capital stock); the `--capital-proxy capcomp` flag exists; `--exclude-years 2008 2009` flag exists.
- **Issues:** #17, #18.
- **Why I'm asking:** Two cheap robustness levers, both already wired. (1) Is `K` (capital stock) the obvious thesis-facing choice and `CAP` (capital compensation) the appendix sensitivity? (2) Does the pre-crisis (2001–2007) subsample belong as a thesis-facing column in §6.2.4 or as an appendix table? My instinct is appendix only — but if she wants it in the main table I should plan for that now.

#### Q9. Pre-period freeze window (1990–1995) — defensible? Alt window in appendix?
- **Numbers:** Code currently freezes coord / ud / adjcov on 1990–1995 means (`code/_wiod_panel_utils.py:293`).
- **Issues:** #14.
- **Why I'm asking:** The May 15 draft has prose drift here (§4.2.3 says "e.g. 2000–2005", §4.3.1 says 1990–1995). I'm going to align everything on 1990–1995 in the prose, but I want her judgement on whether to (a) cite Leibrecht et al. (2023) for the pre-sample-freeze rationale and stop there, or (b) document an alternative window (e.g. 1996–2000) in the appendix as a sensitivity. Option (b) is essentially free to run; it just costs another half-page in the appendix.

#### Q10. Sample-vs-specification decomposition — how to present 0.0124 → 0.0142 → 0.0117 without burying the lede?
- **Numbers:** see headline table at top.
- **Issues:** #13 (smaller writing changes), #11.
- **Why I'm asking:** The "sample makes the coefficient bigger, specification makes it smaller" story is mechanically clean but rhetorically subtle. I'd like her view on whether this lives in §6.2.5, in the appendix, or as a one-paragraph footnote inside the Eq. 2b discussion. Right now I have the full table at `results/_snapshot_20260515/secondary/wiod_eq2_coord_sample_decomposition.md`.

#### Q11. Outcome variable phrasing, GDP control specification, FE structure
- **Numbers:** Outcome = `ln(H_EMPE)` = hours worked by employees (not employment, not exports). Macro control = `gdp_growth` from Eurostat `nama_10_gdp`. FE = country-industry + year.
- **Issues:** #14.
- **Why I'm asking:** Three related prose-mechanics rulings I want to clear in one go. (1) Confirm "hours worked by employees" is the right plain-language phrasing for the dependent variable in §4.2.2 / §5.2.1 (the draft currently says "industry-level gross exports" — leftover from an earlier trade branch). (2) Is GDP growth alone enough as the macro control, or does she want a GDP gap term as well? (3) Country-industry FE + year FE — comfortable as-is, or does she prefer two-way (country × year, industry × year)?

#### Q12. VIF threshold for the §6.2 lead-in, and how to narrate the structurally-high Eq. 2b VIFs
- **Numbers:** Eq. 2b gate reports max FE-style VIF = 1.38 at the gate stage; the multicollinearity in the full Eq. 2b spec (5 robot-related terms incl. the three-way) is structurally higher.
- **Issues:** #22.
- **Why I'm asking:** I want a defensible threshold to cite in the §6.2 lead-in (10 is the textbook default; some authors use 5). The Eq. 2b three-way will push VIF up by construction — I want to know whether she'd rather I (a) report VIFs only for the gate variables, (b) report VIFs for all interaction terms and explain the structural inflation, or (c) skip VIFs entirely and lean on the decomposition diagnostic instead.

### P2 — nice-to-have (final-mile process)

#### Q13. Chapter order, page-length expectations, submission timeline, and pre-submission send
- **Issues:** #12.
- **Why I'm asking:** Logistics. (1) Does §6.2 robustness come before or after §6.1.3 main results? (2) Rough page budget for §6 results and §7 discussion? (3) What does she consider "good enough" given the time budget — full polish on §6 and §7, or rough §7 with §6 watertight? (4) Does she want to see anything from me between today and submission (an interpretation memo? a §6 draft?) or is the meeting itself the last touchpoint?

---

## What I'll bring on screen

In rough display order:

1. **`README.md` § Methodology + Active Workflow** — for the canonical Eq. 1 / Eq. 2 / Eq. 2b specification and per-equation sample counts.
2. **`results/_snapshot_20260515/core/wiod_first_results_overview.md`** — single-page headline summary.
3. **`results/_snapshot_20260515/core/wiod_first_results_summary.csv`** — the exact coefficients and country lists per model.
4. **`results/_snapshot_20260515/tables/wiod_regression_table_combined.md`** and **`wiod_regression_table_combined_clusterstars.md`** — both star variants side by side for the Q1 decision.
5. **`results/_snapshot_20260515/secondary/wiod_eq2_coord_sample_decomposition.md`** — for Q10.
6. **`results/_snapshot_20260515/secondary/wiod_common_sample_robustness.md`** — for Q5 / Q10.
7. **`results/_snapshot_20260515/secondary/wiod_eq2b_coord_ud_comparison.md`** + **`wiod_eq2b_coord_ud_gate.md`** — for Q5.
8. **`.cursor/plans/thesis-restart-verify-and-align_af86781a.plan.md`** — Phase 4 (#9, #10, #11) framing.
9. **The umbrella GitHub issue** (created from this doc) — open in a browser tab so I can take live notes into each sub-issue.
10. The May 15 draft PDF (`context/Master Thesis Draft - May 15.pdf`) at §4.2.2, §4.3.3, §6.2, Appendix 2 — for the prose-drift checkpoints in Q9 / Q11.

---

## Backup list (if there is leftover time)

These are second-tier and I'll only pull them out if we're more than 20 minutes ahead of schedule.

- **B1. Country-jackknife (#16).** What's an acceptable stability band for the coord interaction across one-country-drop subsamples? Does she expect a coefficient plot in §6.2.2 or a min/max/sd summary line?
- **B2. Binary `high_coord_pre` (#19).** If the binary recode flips the sign or moves the magnitude meaningfully, does that change the headline framing, or is the continuous coord interaction always the canonical result?
- **B3. Reviewer-facing limitations language for "21 country gap to Leibrecht's 37"** (draft §8.3) — should I keep that comparison or drop it now that the panel is 26 countries for Eq. 1?
- **B4. KLEMS legacy overlap** — does the appendix still need a KLEMS-WIOD measurement comparison, or is it safe to drop given the active workflow is WIOD-only?
- **B5. Reference benchmark for Eq. 2 ud** — is "reference benchmark institutional result" the right label for the null ud interaction, or would she prefer "robustness" framing?
- **B6. Robustness section ordering** — within §6.2, does she want inference (6.2.1) first, sample (6.2.2) second, specification (6.2.3) third, period (6.2.4) fourth, decomposition (6.2.5) last? That's the draft outline today; just want to confirm.

---

## GitHub issues filed for this meeting

Umbrella (the page to keep open during the meeting):

- **#36 — [Meeting Q] Rebecka 15 May — umbrella** → https://github.com/erik-gunnarsson/msc-thesis/issues/36

Individual question issues, in the same order as the prioritised list above:

### P0
1. **#23 — [Meeting Q] Cluster-vs-wild gap reporting + thesis-facing star policy** → https://github.com/erik-gunnarsson/msc-thesis/issues/23 — labels: `question`, `inference`, `thesis-table`, `writing`
2. **#24 — [Meeting Q] Headline claim language given p_wild = 0.108** → https://github.com/erik-gunnarsson/msc-thesis/issues/24 — labels: `question`, `inference`, `writing`
3. **#25 — [Meeting Q] Few-cluster corrections beyond Rademacher wild (Mammen / CR2)** → https://github.com/erik-gunnarsson/msc-thesis/issues/25 — labels: `question`, `inference`
4. **#26 — [Meeting Q] AdjCov (15-country) status — restricted secondary focal or demote to footnote?** → https://github.com/erik-gunnarsson/msc-thesis/issues/26 — labels: `question`, `inference`, `robustness`, `writing`
5. **#27 — [Meeting Q] Eq. 2b Hawk–Dove placement — appendix-only, short §6.1.5 robustness, or out?** → https://github.com/erik-gunnarsson/msc-thesis/issues/27 — labels: `question`, `robustness`, `writing`
6. **#28 — [Meeting Q] Narrative framing — null Eq. 1 baseline vs positive Eq. 2 coord interaction** → https://github.com/erik-gunnarsson/msc-thesis/issues/28 — labels: `question`, `writing`

### P1
7. **#29 — [Meeting Q] Switzerland exclusion + robot-stock vs robot-intensity as the headline regressor** → https://github.com/erik-gunnarsson/msc-thesis/issues/29 — labels: `question`, `robustness`
8. **#30 — [Meeting Q] Capital proxy K vs CAP + 2008–2009 exclusion (thesis-table column or appendix?)** → https://github.com/erik-gunnarsson/msc-thesis/issues/30 — labels: `question`, `robustness`
9. **#31 — [Meeting Q] Pre-period freeze window (1990–1995) defensibility + alternative window in appendix** → https://github.com/erik-gunnarsson/msc-thesis/issues/31 — labels: `question`, `robustness`, `writing`
10. **#32 — [Meeting Q] Sample-vs-specification decomposition — how to present 0.0124 → 0.0142 → 0.0117 without burying the lede?** → https://github.com/erik-gunnarsson/msc-thesis/issues/32 — labels: `question`, `writing`, `thesis-table`
11. **#33 — [Meeting Q] Outcome variable phrasing, GDP control specification, FE structure** → https://github.com/erik-gunnarsson/msc-thesis/issues/33 — labels: `question`, `writing`
12. **#34 — [Meeting Q] VIF threshold for §6.2 lead-in + structural multicollinearity narration for Eq. 2b** → https://github.com/erik-gunnarsson/msc-thesis/issues/34 — labels: `question`, `inference`, `robustness`

### P2
13. **#35 — [Meeting Q] Final-mile process — chapter order, page budget, submission timeline, pre-submission send** → https://github.com/erik-gunnarsson/msc-thesis/issues/35 — labels: `question`, `writing`

Copy-paste version for the agenda email / Notion:

```
#36 umbrella
P0: #23 #24 #25 #26 #27 #28
P1: #29 #30 #31 #32 #33 #34
P2: #35
```
