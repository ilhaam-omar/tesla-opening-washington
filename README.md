# Opening the Gates: Tesla's charging network and electric car sales in Washington State

Code for *Opening the Gates: Whose Sales Change, and Where, When a Firm Shares Its Proprietary Complement with Rivals*
(ESMA 722 Technology Strategy, Assignment III, Khalifa University, Fall 2026).

Authors: Ilhaam Aziz Omar, Sarah Ahmed Al Kindi, Shamma Abdelrahman AlMaazmi

## What the code does

Tesla opened its fast-charging network to rival carmakers one brand at a time from March 2024. The script uses
these staggered access dates and every new battery electric car registered in Washington State (January 2022 to
June 2025) to test where opening changed rivals', Tesla's, and total sales.

1. **Data and sample (Section 3.2).** Keeps new battery electric cars bought by Washington residents, counts each car
   once at its first registration, and places it in its census tract and month of sale. Groups brands into one unit
   per carmaker and links each unit to its access date.
2. **Measures (Section 3.3).** For each tract, fixed at 31 December 2023:
   *Commercial alternatives* (other companies' share of usable fast-charging ports within 25 miles),
   *Home charging* (share of homes that are owner-occupied one-unit houses), and the controls
   (income, density, Tesla V3/V4 stalls, county vote share; brand price and number of models).
3. **Estimation (Section 3.4).** Poisson models with fixed effects:
   * Eq. (1), rival side: H1a and H2a, plus a stricter version with county-month and brand-month effects.
   * Eq. (2), owner side: H1b and H2b; the same model with total sales tests H3a and H3b.
   * Checks: clustering choices, announcement dates instead of access dates, plug-in hybrid placebos, and event studies.

## Results summary

| Hypothesis | Estimate | Verdict |
|---|---|---|
| Baseline (rivals after access) | -1.9% (p = 0.43) | reported |
| H1a | -0.6% (p = 0.88); stricter -4.6% (p = 0.14) | not supported |
| H1b | -1.0% per brand (p = 0.09) | not supported |
| H2a | +5.8% (p < 0.001); stricter +6.1% (p = 0.06) | weak support |
| H2b | -1.6% per brand (p < 0.001) | supported |
| H3a | -1.3% per brand (p = 0.007) | supported by point estimate; no clear break in the event study |
| H3b | -0.3% per brand (p = 0.47) | supported (no market expansion) |

Full output: [`output/log.txt`](output/log.txt).

## How to run

```bash
pip install -r requirements.txt
python analysis.py          # about 10-20 minutes
```

Place the input files in `data/` first (see [`data/README.md`](data/README.md)). Results are written to `output/`.
