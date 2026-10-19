* =============================================================================
* part1.do  --  Part 1: internet access and reported crimes against women
*
*   1a  Model 1: did cyber crime against women grow faster in more-connected States?
*       (State x crime x year, 2017-2024; offline crimes against women as comparison)
*   1b  Across States: do better-connected States record more cyber crime against women?
*   1c  Within States: TRAI connections 2022-2024, Delhi + Haryana merged
*   1d  India by year: internet users and cyber crime against women (chart)
*
* Run from the repository root:   do stata/part1.do
* Needs (once): ssc install ftools ; ssc install reghdfe ; ssc install ppmlhdfe
* Output: stata/part1_results.txt (log), stata/part1_national.png
* Python equivalent: scripts/estimate_models.py (1a), scripts/access_checks.py (1b-1d).
* =============================================================================

version 16
clear all
set more off
* Run from the repository root; if Stata is in the stata folder itself, step up one level.
capture confirm file "stata/state_year_panel.dta"
if _rc {
    capture confirm file "state_year_panel.dta"
    if !_rc cd ..
    else {
        display as error "Cannot find the stata folder: cd to the folder that contains it, then run again"
        exit 601
    }
}
capture log close
log using "stata/part1_results.txt", text replace

foreach p in ftools reghdfe ppmlhdfe {
    capture which `p'
    if _rc ssc install `p', replace
}

* Standardise a State-level exposure within the current sample: mean 0, SD 1 across States,
* so exp(b) = rate ratio per SD.
capture program drop zstate
program define zstate
    args x
    capture drop z _tag
    egen _tag = tag(state)
    quietly summarize `x' if _tag
    generate double z = (`x' - r(mean)) / r(sd)
    drop _tag
end

* Standardise a State-level variable into a new variable (mean 0, SD 1 across States)
capture program drop zas
program define zas
    args x newname
    capture drop `newname' _tag
    egen _tag = tag(state)
    quietly summarize `x' if _tag
    generate double `newname' = (`x' - r(mean)) / r(sd)
    drop _tag
end

* Fixed-effect identifiers: State x category, State x year, category x year; numeric State id
capture program drop makefe
program define makefe
    capture drop sc st ct sid
    egen sc = group(state category)
    egen st = group(state year)
    egen ct = group(category year)
    egen sid = group(state)
end

* =============================================================================
* 1a  MODEL 1
*   cases = Cyber x Access x (year - 2017) | State x category, State x year, category x year
*   Cyber = all cyber crimes against women summed into one category.
*   Expected (Python): CAMS 15+ RR 0.97 per year, p = 0.38.
* =============================================================================
use "stata/state_category_year_panel.dta", clear
keep if inlist(category_group, "cyber_women", "offline_women")
replace category = "cyber crimes against women (all)" if category_group == "cyber_women"
collapse (sum) cases (first) access_cams2023_15plus access_nss2017_5plus access_nfhs5_15to49_avg ///
    access_cams2023_15to24, by(state year category category_group)
generate cyber = category_group == "cyber_women"
makefe
tempfile m1
save `m1'

display _n "==================== 1a MODEL 1: by access measure ===================="
foreach x in access_cams2023_15plus access_nss2017_5plus access_nfhs5_15to49_avg access_cams2023_15to24 {
    use `m1', clear
    keep if !missing(`x')
    zstate `x'
    generate double treat = cyber * z * (year - 2017)
    display _n "--- Model 1, exposure: `x'"
    ppmlhdfe cases treat, absorb(sc st ct) vce(cluster sid)
    display "Rate ratio per SD per year: " %6.3f exp(_b[treat])
}

* Model 1 with controls: income and urban share, interacted like access (33 States)
*   Expected (Python): access 0.95 (p = 0.54), income 0.99 (0.79), urban 1.04 (0.60).
use `m1', clear
merge m:1 state using "stata/state_controls.dta", keep(master match) nogenerate
generate double ln_income = ln(nsdp_pc_avg)
keep if !missing(ln_income, urban_share_cams)
keep if !missing(access_cams2023_15plus)
zas access_cams2023_15plus z_access
zas ln_income z_income
zas urban_share_cams z_urban
generate double treat = cyber * z_access * (year - 2017)
generate double treat_inc = cyber * z_income * (year - 2017)
generate double treat_urb = cyber * z_urban * (year - 2017)
display _n "--- Model 1 with income and urban share controls"
ppmlhdfe cases treat treat_inc treat_urb, absorb(sc st ct) vce(cluster sid)

* Each cyber head separately against offline crimes
display _n "--- Model 1 by crime type (CAMS 15+)"
use "stata/state_category_year_panel.dta", clear
keep if inlist(category_group, "cyber_women", "offline_women") & !missing(access_cams2023_15plus)
tempfile heads
save `heads'
levelsof category if category_group == "cyber_women", local(cyberheads)
foreach h of local cyberheads {
    use `heads', clear
    keep if category == "`h'" | category_group == "offline_women"
    generate cyber = category_group == "cyber_women"
    makefe
    zstate access_cams2023_15plus
    generate double treat = cyber * z * (year - 2017)
    display _n "--- head: `h'"
    ppmlhdfe cases treat, absorb(sc st ct) vce(cluster sid)
    display "Rate ratio: " %6.3f exp(_b[treat])
}

* Event study, base year 2017
use `m1', clear
keep if !missing(access_cams2023_15plus)
zstate access_cams2023_15plus
forvalues y = 2018/2024 {
    generate double es`y' = cyber * z * (year == `y')
}
display _n "--- Model 1 event study (base 2017)"
ppmlhdfe cases es2018-es2024, absorb(sc st ct) vce(cluster sid)

* Placebo: cyber fraud in place of cyber crime against women
use "stata/state_category_year_panel.dta", clear
keep if inlist(category_group, "cyber_placebo", "offline_women")
generate cyber = category_group == "cyber_placebo"
makefe
keep if !missing(access_cams2023_15plus)
zstate access_cams2023_15plus
generate double treat = cyber * z * (year - 2017)
display _n "--- Model 1 placebo: cyber fraud (expected 1.06, p = 0.61)"
ppmlhdfe cases treat, absorb(sc st ct) vce(cluster sid)

* Robustness
foreach r in drop2020 drop2024 dropKATG {
    use `m1', clear
    keep if !missing(access_cams2023_15plus)
    if "`r'" == "drop2020" drop if year == 2020
    if "`r'" == "drop2024" drop if year == 2024
    if "`r'" == "dropKATG" drop if inlist(state, "Karnataka", "Telangana")
    zstate access_cams2023_15plus
    generate double treat = cyber * z * (year - 2017)
    display _n "--- Model 1 robustness: `r'"
    ppmlhdfe cases treat, absorb(sc st ct) vce(cluster sid)
}

* Labelling controls (break States from stata/labelling_breaks.dta)
use `m1', clear
keep if !missing(access_cams2023_15plus)
merge m:1 state year using "stata/labelling_breaks.dta", keep(master match) nogenerate
replace regime = 0 if missing(regime)
bysort state: egen breakstate = max(label_break)
replace breakstate = 0 if missing(breakstate)
foreach v in other_share it_share {
    quietly summarize `v'
    replace `v' = r(mean) if missing(`v')
}
generate double cyb_other = cyber * other_share
generate double cyb_it = cyber * it_share
egen scr = group(state category regime)
tempfile lab1
save `lab1'

display _n "--- Model 1 labelling: drop the 17 States with breaks (expected 0.94, p = 0.22)"
keep if breakstate == 0
zstate access_cams2023_15plus
generate double treat = cyber * z * (year - 2017)
ppmlhdfe cases treat, absorb(sc st ct) vce(cluster sid)

use `lab1', clear
zstate access_cams2023_15plus
generate double treat = cyber * z * (year - 2017)
display _n "--- Model 1 labelling: State x category x regime fixed effects (expected 0.95, p = 0.25)"
ppmlhdfe cases treat, absorb(scr st ct) vce(cluster sid)
display _n "--- Model 1 labelling: control for the 'other' share (expected 0.96, p = 0.29)"
ppmlhdfe cases treat cyb_other, absorb(sc st ct) vce(cluster sid)
display _n "--- Model 1 labelling: regime FE + 'other' and IT Act shares (expected 0.94, p = 0.13)"
ppmlhdfe cases treat cyb_other cyb_it, absorb(scr st ct) vce(cluster sid)

* =============================================================================
* 1b  ACROSS STATES (levels), 2017-2024
*   cases = Access (standardised) | year, exposure = population, SE clustered by State
*   Expected (Python), CAMS 15+: cyber crime against women 1.54 (p = 0.010);
*   offline crimes against women 1.05 (p = 0.77).
* =============================================================================
display _n "==================== 1b ACROSS STATES ===================="
use "stata/state_year_panel.dta", clear
keep if year >= 2017
egen sid = group(state)
tempfile sy
save `sy'
foreach x in access_cams2023_15plus access_nss2017_5plus access_nfhs5_15to49_avg {
    foreach y in cyber_vaw_cases offline_vaw_cases cyber_total_cases cyber_fraud {
        local off female_pop_lakh
        if inlist("`y'", "cyber_total_cases", "cyber_fraud") local off population_lakh
        use `sy', clear
        keep if !missing(`x', `y', `off') & `off' > 0
        zstate `x'
        display _n "--- 1b, access: `x', outcome: `y'"
        ppmlhdfe `y' z, absorb(year) exposure(`off') vce(cluster sid)
        display "Rate ratio per SD: " %6.3f exp(_b[z])
    }
}

* 1b with controls: income (log per capita NSDP, RBI) and urban share (CAMS-implied), 33 States.
*   Expected (Python), cyber crime against women: access 1.56 (p = 0.010) without controls;
*   + income: access 0.64 (0.26), income 2.55 (0.021); + urban: access 1.57 (0.025);
*   + both: access 0.84 (0.63), income 3.45 (0.004), urban 0.44 (0.034).
*   Offline crimes with both controls: access 0.92 (0.81).
foreach y in cyber_vaw_cases offline_vaw_cases {
    use `sy', clear
    merge m:1 state using "stata/state_controls.dta", keep(master match) nogenerate
    generate double ln_income = ln(nsdp_pc_avg)
    keep if !missing(ln_income, urban_share_cams)
    keep if !missing(access_cams2023_15plus, `y')
    zas access_cams2023_15plus z_access
    zas ln_income z_income
    zas urban_share_cams z_urban
    display _n "--- 1b with controls, outcome: `y'"
    ppmlhdfe `y' z_access, absorb(year) exposure(female_pop_lakh) vce(cluster sid)
    ppmlhdfe `y' z_access z_income, absorb(year) exposure(female_pop_lakh) vce(cluster sid)
    ppmlhdfe `y' z_access z_urban, absorb(year) exposure(female_pop_lakh) vce(cluster sid)
    ppmlhdfe `y' z_access z_income z_urban, absorb(year) exposure(female_pop_lakh) vce(cluster sid)
}

* 1b with police capacity (BPR&D 2024): cyber police units per crore and civil police per lakh (2020)
*   Expected (Python), cyber crime against women, access + income + cyber units + police:
*   access 0.89 (0.76), income 2.23 (<0.001), cyber units 0.67 (0.027), police 0.84 (0.70).
foreach y in cyber_vaw_cases offline_vaw_cases {
    use `sy', clear
    merge m:1 state using "stata/state_controls.dta", keep(master match) nogenerate
    merge m:1 state using "stata/state_police.dta", keep(master match) nogenerate
    generate double ln_income = ln(nsdp_pc_avg)
    generate double ln_police = ln(civil_police_per_lakh_2020)
    generate double ln_cyber_units = ln(1 + cyber_units_per_crore)
    keep if !missing(access_cams2023_15plus, `y', ln_income, ln_police)
    zas access_cams2023_15plus z_access
    zas ln_income z_income
    zas ln_police z_police
    zas ln_cyber_units z_cyber
    display _n "--- 1b with police capacity, outcome: `y'"
    ppmlhdfe `y' z_cyber z_police, absorb(year) exposure(female_pop_lakh) vce(cluster sid)
    ppmlhdfe `y' z_access z_income z_cyber z_police, absorb(year) exposure(female_pop_lakh) vce(cluster sid)
}

* =============================================================================
* 1c  WITHIN STATES: TRAI connections, 2022-2024
*   cases = TRAI connections per 100 (per 10) | State, year; exposure = female population
*   Delhi and Haryana merged: TRAI's Delhi licence area includes Gurgaon and Faridabad (Haryana)
*   and Noida and Ghaziabad (UP), and TRAI's State-wise counts moved subscriptions from Delhi to
*   Haryana (see analysis/models/README.md). Dec 2021 excluded (TRAI misallocation).
*   Expected (Python): merged 1.30 (p = 0.034); unmerged 1.16 (0.001); drop Delhi 1.11 (0.50);
*   with UP 1.29 (0.22); offline placebo 1.13 (0.030); capacity control 1.18 (0.14);
*   cyber vs offline 1.05 (0.73).
* =============================================================================
display _n "==================== 1c WITHIN STATES (TRAI) ===================="
use "stata/state_year_panel.dta", clear
keep if inrange(year, 2022, 2024) & !missing(trai_subs_per100, cyber_vaw_cases)
generate double subs_mn = trai_subs_per100 * population_lakh / 1000
keep state year cyber_vaw_cases offline_vaw_cases cyber_total_cases female_pop_lakh population_lakh subs_mn
tempfile trai
save `trai'

foreach v in merged unmerged dropdelhi withup {
    use `trai', clear
    if "`v'" == "merged" replace state = "Delhi+Haryana" if inlist(state, "Delhi", "Haryana")
    if "`v'" == "dropdelhi" drop if state == "Delhi"
    if "`v'" == "withup" replace state = "Delhi+Haryana+UP" if inlist(state, "Delhi", "Haryana", "Uttar Pradesh")
    collapse (sum) cyber_vaw_cases offline_vaw_cases cyber_total_cases female_pop_lakh population_lakh subs_mn, ///
        by(state year)
    generate double trai_10 = subs_mn * 1000 / population_lakh / 10
    generate double other_cyber = ln(cyber_total_cases - cyber_vaw_cases + 1)
    egen sid = group(state)
    display _n "--- 1c, version: `v'"
    ppmlhdfe cyber_vaw_cases trai_10, absorb(sid year) exposure(female_pop_lakh) vce(cluster sid)
    display "Rate ratio per 10 connections per 100: " %6.3f exp(_b[trai_10])
    if "`v'" == "merged" {
        tempfile merged
        save `merged'
        display _n "--- 1c placebo: offline crimes against women (merged)"
        ppmlhdfe offline_vaw_cases trai_10, absorb(sid year) exposure(female_pop_lakh) vce(cluster sid)
        display _n "--- 1c control for growth in other cyber crime (recording capacity)"
        ppmlhdfe cyber_vaw_cases trai_10 other_cyber, absorb(sid year) exposure(female_pop_lakh) vce(cluster sid)
    }
}

* Cyber versus offline in one model (merged)
use `merged', clear
expand 2, generate(cyber)
generate double cases = cond(cyber, cyber_vaw_cases, offline_vaw_cases)
generate double tc = trai_10 * cyber
egen sc = group(sid cyber)
egen st = group(sid year)
egen ct = group(cyber year)
display _n "--- 1c cyber vs offline crimes against women"
ppmlhdfe cases tc, absorb(sc st ct) vce(cluster sid)
display "Rate ratio: " %6.3f exp(_b[tc])

* =============================================================================
* 1d  INDIA BY YEAR, 2017-2024: internet users and cyber crime against women
*   Expected (Python): elasticity 0.99, correlation of logs 0.97, correlation of growth 0.28.
* =============================================================================
display _n "==================== 1d INDIA BY YEAR ===================="
use "stata/national_year.dta", clear
keep if inrange(year, 2017, 2024)
tsset year
generate double l_users = ln(internet_users_mn)
generate double l_cyber = ln(cyber_vaw_cases)
generate double l_offline = ln(offline_vaw_cases)
list year internet_users_mn cyber_vaw_cases offline_vaw_cases, noobs sep(0)
correlate l_users l_cyber l_offline
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
