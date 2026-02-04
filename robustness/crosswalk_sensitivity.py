'''
Do it after you’ve built the weights and before you freeze the final regression panel — basically once you can run your baseline regression end-to-end at least once.

1) Crosswalk sensitivity (recommended)
Effort: Low
What you need: your crosswalk table (US industry → NACE2) plus a way to compute “mapping messiness.”

How it works (minimal version):

For each NACE2 industry, compute:

# of US source industries mapping into it, or

HHI / concentration of the weights used to build its EU weight (e.g., if 1 US industry accounts for 90% of the mapping, it’s “clean”; if 10 industries each contribute 10%, it’s “messy”).

Define “messy” as top quartile (or top 20%).

Re-estimate your main model dropping messy industries.

Report: main coefficient and interaction are similar in sign and broadly similar magnitude.

Why this is powerful: it directly targets the “US → EU mapping” apples/oranges critique (measurement validity; secondary data limitations in the textbook).

Risk: you may lose some industries → less power, but it’s still a credible check.


'''