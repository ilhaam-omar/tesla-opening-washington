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
   * Eq. (1), rival side: whether a rival's market share rises after it gains access (H1), and where it rises more
     (H1a, H1b). The area-month effects hold each neighborhood's whole market fixed every month, so the estimates
     are changes in market share.
   * Eq. (2), owner side: where Tesla's market share falls more as rivals gain access (H2a, H2b), using Tesla's
     registrations with total registrations as an offset; the same model with total registrations tests where total
     sales rise more (H3a, H3b).
   * Checks: clustering choices, announcement dates instead of access dates, plug-in hybrid placebos, a pre-access
     trend, quarterly event studies, Tesla counts instead of shares, and a county measure of home charging
     (Ge et al., 2024).

The owner's and total-sales main effects are not tested: every neighborhood had the same number of brands with access
in a given month, so a statewide change cannot be separated from other statewide trends.

## Results summary

| Hypothesis | Estimate | Supported |
|---|---|---|
| H1: a rival's market share rises after it gains access | -1.9% (p = 0.43) | No |
| H1a: ...more where commercial alternatives are scarce | -0.6% (p = 0.88); stricter -4.6% (p = 0.14) | No |
| H1b: ...more where private provision is common | +5.8% (p < 0.001); stricter +6.1% (p = 0.06) | Weak |
| H2a: the owner's share falls more where commercial alternatives are scarce | -0.1% per brand (p = 0.84) | No |
| H2b: the owner's share falls more where private provision is common | -1.3% per brand (p < 0.001); about -11% with nine brands | Yes |
| H3a: total sales rise more where commercial alternatives are scarce | -1.3% per brand (p = 0.007); about +12.5% with nine brands | Yes (no clear break in the event study) |
| H3b: total sales rise less where private provision is common | -0.3% per brand (p = 0.47) | No |

Full output: [`output/log.txt`](output/log.txt).

## How to run

```bash
pip install -r requirements.txt
python analysis.py
```

All input files are in `data/` (see [`data/README.md`](data/README.md)). Results are written to `output/`.
The run takes about two minutes.
