* =============================================================================
* part1.do  --  Part 1: internet access and recorded cyber crime against women
*   Follows the Methodology, Part 1:
*     Step 1  Across States: levels, then income, urban share and police capacity as controls
*     Step 2  Growth within States (Model 1), with checks
*     Step 3  Changes in connections (TRAI 2022-2024), Delhi and Haryana combined
*     Trend   India by year (descriptive)
* Run from the repository root:   do stata/part1.do
* Output: stata/part1_results.txt, stata/part1_national.png
* Each model prints its rate ratio; "Expected" lines give the Python result to compare.
* =============================================================================

run stata/setup.do
capture log close
log using "stata/part1_results.txt", text replace

* =============================================================================
* STEP 1  ACROSS STATES, 2017-2024
*   cases = Access (and controls) | year;  exposure = female population;  SE clustered by State
* =============================================================================
display _n "==================== STEP 1: ACROSS STATES ===================="
use "stata/state_year_panel.dta", clear
keep if inrange(year, 2017, 2024)
merge_ctl
egen sid = group(state)
tempfile sy
save `sy'

* (a) No controls, all 35 States. Expected: cyber 1.54 (p = 0.010); offline 1.05 (p = 0.77)
foreach y in cyber_vaw_cases offline_vaw_cases {
    use `sy', clear
    keep if !missing(access_cams2023_15plus, `y')
    zas access_cams2023_15plus z_access
    display _n "--- Step 1(a), outcome: `y'"
    ppmlhdfe `y' z_access, absorb(year) exposure(female_pop_lakh) vce(cluster sid)
    display "Rate ratio per SD of access: " %6.3f exp(_b[z_access])
}

* (b) With controls, 33 States (RBI publishes no income for Lakshadweep, DNH-DD).
* Expected, cyber crime against women:
*   + income:                    access 0.64 (0.26), income 2.55 (0.021)
*   + income, urban:             access 0.84 (0.63), income 3.45 (0.004), urban 0.44 (0.034)
*   + income, cyber units, police: access 0.89 (0.76), income 2.23 (<0.001), cyber units 0.67 (0.027), police 0.84 (0.70)
*   all five:                    access 1.10 (0.79), income 2.75 (<0.001), urban 0.52 (0.031), cyber units 0.70 (0.025), police 0.92 (0.83)
* Offline crimes against women: no variable significant.
foreach y in cyber_vaw_cases offline_vaw_cases {
    use `sy', clear
    keep if !missing(access_cams2023_15plus, `y', ln_income, urban_share_cams, ln_police, ln_cyber_units)
    zas access_cams2023_15plus z_access
    zas ln_income z_income
    zas urban_share_cams z_urban
    zas ln_police z_police
    zas ln_cyber_units z_cyber
    display _n "--- Step 1(b), outcome: `y'"
    ppmlhdfe `y' z_access z_income, absorb(year) exposure(female_pop_lakh) vce(cluster sid)
    ppmlhdfe `y' z_access z_income z_urban, absorb(year) exposure(female_pop_lakh) vce(cluster sid)
    ppmlhdfe `y' z_access z_income z_cyber z_police, absorb(year) exposure(female_pop_lakh) vce(cluster sid)
    ppmlhdfe `y' z_access z_income z_urban z_cyber z_police, absorb(year) exposure(female_pop_lakh) vce(cluster sid)
}

* =============================================================================
* STEP 2  GROWTH WITHIN STATES (MODEL 1), 2017-2024
*   cases = exp(b x Cyber x Access x (year - 2017) + State x crime + State x year + crime x year)
*   Expected: CAMS 15+ 0.97 (p = 0.37); NSS 0.98 (0.54); NFHS-5 1.02 (0.59); CAMS 15-24 0.97 (0.35)
* =============================================================================
display _n "==================== STEP 2: MODEL 1 ===================="
build_m
fe_ids
tempfile m1
save `m1'

foreach x in access_cams2023_15plus access_nss2017_5plus access_nfhs5_15to49_avg access_cams2023_15to24 {
    use `m1', clear
    keep if !missing(`x')
    zas `x' z
    generate double treat = cyber * z * (year - 2017)
    display _n "--- Model 1, access: `x'"
    ppmlhdfe cases treat, absorb(sc st ct) vce(cluster sid)
    display "Rate ratio per SD per year: " %6.3f exp(_b[treat])
}

* Check: each cyber crime type against offline crimes (all between 0.89 and 1.01, none significant)
use "stata/state_category_year_panel.dta", clear
keep if inlist(category_group, "cyber_women", "offline_women") & !missing(access_cams2023_15plus)
tempfile heads
save `heads'
levelsof category if category_group == "cyber_women", local(types)
foreach h of local types {
    use `heads', clear
    keep if category == "`h'" | category_group == "offline_women"
    generate cyber = category_group == "cyber_women"
    fe_ids
    zas access_cams2023_15plus z
    generate double treat = cyber * z * (year - 2017)
    display _n "--- Model 1, type: `h'"
    ppmlhdfe cases treat, absorb(sc st ct) vce(cluster sid)
}

* Check: cyber fraud in place of cyber crime against women. Expected 1.06 (p = 0.61)
build_m, placebo
fe_ids
keep if !missing(access_cams2023_15plus)
zas access_cams2023_15plus z
generate double treat = cyber * z * (year - 2017)
display _n "--- Model 1 placebo: cyber fraud"
ppmlhdfe cases treat, absorb(sc st ct) vce(cluster sid)

* Check: drop 2020, drop 2024, drop Karnataka and Telangana. Expected 0.96-0.97, p 0.30-0.43
foreach r in drop2020 drop2024 dropKATG {
    use `m1', clear
    keep if !missing(access_cams2023_15plus)
    if "`r'" == "drop2020" drop if year == 2020
    if "`r'" == "drop2024" drop if year == 2024
    if "`r'" == "dropKATG" drop if inlist(state, "Karnataka", "Telangana")
    zas access_cams2023_15plus z
    generate double treat = cyber * z * (year - 2017)
    display _n "--- Model 1 check: `r'"
    ppmlhdfe cases treat, absorb(sc st ct) vce(cluster sid)
}

* =============================================================================
* STEP 3  CHANGES IN CONNECTIONS (TRAI), 2022-2024
*   cases = TRAI connections per 100 (per 10) | State + year;  exposure = female population
*   Delhi and Haryana combined: TRAI's Delhi licence area includes Gurgaon and Faridabad, and
*   TRAI's State counts moved about 8 million connections from Delhi to Haryana in 2023-2025.
*   Expected: combined 1.30 (p = 0.034); offline placebo 1.13 (0.030);
*   control for other cyber crime 1.18 (0.14); as reported 1.16 (0.001); drop Delhi 1.11 (0.50);
*   Delhi + Haryana + UP 1.29 (0.22)
* =============================================================================
display _n "==================== STEP 3: TRAI CONNECTIONS ===================="
use "stata/state_year_panel.dta", clear
keep if inrange(year, 2022, 2024) & !missing(trai_subs_per100, cyber_vaw_cases)
generate double subs_mn = trai_subs_per100 * population_lakh / 1000
keep state year cyber_vaw_cases offline_vaw_cases cyber_total_cases female_pop_lakh population_lakh subs_mn
tempfile trai
save `trai'

foreach v in combined reported dropdelhi withup {
    use `trai', clear
    if "`v'" == "combined" replace state = "Delhi+Haryana" if inlist(state, "Delhi", "Haryana")
    if "`v'" == "dropdelhi" drop if state == "Delhi"
    if "`v'" == "withup" replace state = "Delhi+Haryana+UP" if inlist(state, "Delhi", "Haryana", "Uttar Pradesh")
    collapse (sum) cyber_vaw_cases offline_vaw_cases cyber_total_cases female_pop_lakh population_lakh subs_mn, ///
        by(state year)
    generate double trai_10 = subs_mn * 1000 / population_lakh / 10
    generate double other_cyber = ln(cyber_total_cases - cyber_vaw_cases + 1)
    egen sid = group(state)
    display _n "--- Step 3, version: `v'"
    ppmlhdfe cyber_vaw_cases trai_10, absorb(sid year) exposure(female_pop_lakh) vce(cluster sid)
    display "Rate ratio per 10 connections per 100: " %6.3f exp(_b[trai_10])
    if "`v'" == "combined" {
        display _n "--- Step 3 check: offline crimes against women"
        ppmlhdfe offline_vaw_cases trai_10, absorb(sid year) exposure(female_pop_lakh) vce(cluster sid)
        display _n "--- Step 3 check: control for growth in other cyber crime"
        ppmlhdfe cyber_vaw_cases trai_10 other_cyber, absorb(sid year) exposure(female_pop_lakh) vce(cluster sid)
    }
}

* =============================================================================
* TREND  INDIA BY YEAR, 2017-2024 (descriptive)
*   Expected: elasticity 0.99; correlation of logs 0.97; correlation of yearly growth 0.28
* =============================================================================
display _n "==================== INDIA BY YEAR ===================="
use "stata/national_year.dta", clear
keep if inrange(year, 2017, 2024)
tsset year
generate double l_users = ln(internet_users_mn)
generate double l_cyber = ln(cyber_vaw_cases)
list year internet_users_mn cyber_vaw_cases offline_vaw_cases, noobs sep(0)
correlate l_users l_cyber
regress l_cyber l_users
generate double g_users = D.l_users
generate double g_cyber = D.l_cyber
correlate g_users g_cyber
twoway (connected cyber_vaw_cases year, yaxis(1)) (connected internet_users_mn year, yaxis(2)), ///
    ytitle("Cyber crimes against women (NCRB)", axis(1)) ytitle("Internet users, million", axis(2)) ///
    xtitle("") legend(order(1 "Cyber crimes against women" 2 "Internet users")) ///
    title("India: internet users and recorded cyber crime against women")
graph export "stata/part1_national.png", replace width(1600)

log close
