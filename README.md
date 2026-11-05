# Input data

All files the code needs are in this folder. Two were trimmed to stay under GitHub's file-size limit;
`prepare_data.py` rebuilds them from the original downloads.

| File | Source | Changes |
|---|---|---|
| `01_WA_DOL_new_EV_registrations_trimmed.csv.gz` | Washington State Department of Licensing, Electric Vehicle Title and Registration Activity (data.wa.gov) | Trimmed: new cars, original titles, Washington residents, sold Jan 2022 to Jun 2025, and the 10 columns used. The full download is 164 MB. |
| `02_AFDC_charging_stations_US_2023-12-31.csv` | U.S. Department of Energy, Alternative Fuels Data Center, stations as of 31 Dec 2023 (afdc.energy.gov/data_download) | None |
| `03_supercharge_info_Tesla_sites.json` | Supercharge.info site list (supercharge.info) | None |
| `04_NREL_home_charging_access_WA_counties.csv` | Ge, Wood & Borlaug (2024), County EV home charging access shares (doi:10.7799/2483609) | Trimmed: Washington counties only. The full workbook is 30 MB. |
| `05_ACS_2022_5yr_B25032_housing_tenure_WA_tracts/` | U.S. Census Bureau, ACS 2018-2022 5-year, Table B25032 (data.census.gov) | None |
| `06_ACS_2022_5yr_B19013_median_income_WA_tracts/` | U.S. Census Bureau, ACS 2018-2022 5-year, Table B19013 (data.census.gov) | None |
| `07_MIT_county_presidential_returns_2000-2024.csv` | MIT Election Data and Science Lab (doi:10.7910/DVN/VOQCHQ) | None |
| `08_access_dates_by_manufacturer.xlsx` | Compiled by the authors from carmakers' press releases | None |
| `09_Census_gazetteer_2022_WA_tract_coordinates.txt` | U.S. Census Bureau, 2022 Gazetteer Files, census tracts | None |
