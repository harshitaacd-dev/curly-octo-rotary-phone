* =============================================================================
* part2.do  --  Part 2: the generative-AI boom and reported crimes against women
*
*   2a  Model 2: did cyber crime against women rise more after 2022 in States that were
*       more connected before the boom? (State x crime x year, 2017-2024)
*   2b  Labelling controls: NCRB recording breaks, and stable versus unstable States
*
* Run from the repository root:   do stata/part2.do
* Needs (once): ssc install ftools ; ssc install reghdfe ; ssc install ppmlhdfe
* Optional randomisation inference: ssc install ritest (block at the end)
* Output: stata/part2_results.txt (log), stata/part2_event_study.csv
* Python equivalent: scripts/estimate_models.py
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
log using "stata/part2_results.txt", text replace

foreach p in ftools reghdfe ppmlhdfe {
    capture which `p'
    if _rc ssc install `p', replace
}

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

capture program drop makefe
program define makefe
    capture drop sc st ct sid
    egen sc = group(state category)
    egen st = group(state year)
    egen ct = group(category year)
    egen sid = group(state)
end

local exposures access_nfhs5_15to49_avg access_cams2023_15plus ads_nudify_to_genai_post ///
    ads_nudify_per_lakh_post trends_deepfake_awareness_pre trends_face_swap_pre

* ---------------------------------------------------------------- build the Model 2 sample
* Treated: all cyber crimes against women summed into one category; comparison: offline crimes.
use "stata/state_category_year_panel.dta", clear
keep if inlist(category_group, "cyber_women", "offline_women")
replace category = "cyber crimes against women (all)" if category_group == "cyber_women"
collapse (sum) cases (first) `exposures', by(state year category category_group)
generate ai = category_group == "cyber_women"
generate post = year >= 2023
makefe
tempfile m2
save `m2'

* =============================================================================
* 2a  MODEL 2
*   cases = AI x Post x Exposure | State x category, State x year, category x year
*   Expected (Python): NFHS-5 access RR 1.07, p = 0.72; pre-trend test p = 0.74.
* =============================================================================
display _n "==================== 2a MODEL 2: by exposure measure ===================="
foreach x of local exposures {
    use `m2', clear
    keep if !missing(`x')
    zstate `x'
    generate double treat = ai * post * z
    display _n "--- Model 2, exposure: `x'"
    ppmlhdfe cases treat, absorb(sc st ct) vce(cluster sid)
    display "Rate ratio per SD after 2022: " %6.3f exp(_b[treat])
}

* Model 2 with controls: income and urban share, interacted like access (33 States)
*   Expected (Python): access 1.23 (p = 0.25), income 0.93 (0.71), urban 0.86 (0.52).
use `m2', clear
merge m:1 state using "stata/state_controls.dta", keep(master match) nogenerate
generate double ln_income = ln(nsdp_pc_avg)
keep if !missing(ln_income, urban_share_cams)
keep if !missing(access_nfhs5_15to49_avg)
zas access_nfhs5_15to49_avg z_access
zas ln_income z_income
zas urban_share_cams z_urban
generate double treat = ai * post * z_access
generate double treat_inc = ai * post * z_income
generate double treat_urb = ai * post * z_urban
display _n "--- Model 2 with income and urban share controls"
ppmlhdfe cases treat treat_inc treat_urb, absorb(sc st ct) vce(cluster sid)
display "Rate ratio (access): " %6.3f exp(_b[treat])

* Model 2 with police capacity (BPR&D): civil police per lakh 2020, cyber police units per crore
*   Exploratory. Expected (Python): access + police: access 1.42 (p = 0.041), police 0.57 (0.011);
*   access alone in the same States 1.08 (0.72). See analysis/models/README.md.
use `m2', clear
merge m:1 state using "stata/state_police.dta", keep(master match) nogenerate
generate double ln_police = ln(civil_police_per_lakh_2020)
generate double ln_cyber_units = ln(1 + cyber_units_per_crore)
keep if !missing(access_nfhs5_15to49_avg, ln_police)
zas access_nfhs5_15to49_avg z_access
zas ln_police z_police
zas ln_cyber_units z_cyber
generate double treat = ai * post * z_access
generate double treat_pol = ai * post * z_police
generate double treat_cyb = ai * post * z_cyber
display _n "--- Model 2 with civil police per lakh"
ppmlhdfe cases treat treat_pol, absorb(sc st ct) vce(cluster sid)
display _n "--- Model 2 with civil police and cyber police units"
ppmlhdfe cases treat treat_pol treat_cyb, absorb(sc st ct) vce(cluster sid)
display _n "--- Event study with police control (pre-trend test)"
foreach y in 2017 2018 2019 2020 2021 2023 2024 {
    generate double es`y' = ai * z_access * (year == `y')
    generate double ep`y' = ai * z_police * (year == `y')
}
ppmlhdfe cases es2017 es2018 es2019 es2020 es2021 es2023 es2024 ep2017 ep2018 ep2019 ep2020 ep2021 ep2023 ep2024, absorb(sc st ct) vce(cluster sid)
test es2017 es2018 es2019 es2020 es2021

* Event study, base year 2022, with joint pre-trend test
foreach x in access_nfhs5_15to49_avg ads_nudify_to_genai_post {
    use `m2', clear
    keep if !missing(`x')
    zstate `x'
    foreach y in 2017 2018 2019 2020 2021 2023 2024 {
        generate double es`y' = ai * z * (year == `y')
    }
    display _n "--- Model 2 event study (base 2022), exposure: `x'"
    ppmlhdfe cases es2017 es2018 es2019 es2020 es2021 es2023 es2024, absorb(sc st ct) vce(cluster sid)
    display "Joint pre-trend test (2017-2021 = 0):"
    test es2017 es2018 es2019 es2020 es2021
    if "`x'" == "access_nfhs5_15to49_avg" {
        preserve
            clear
            set obs 8
            generate year = 2016 + _n
            generate double coef = 0
            generate double se = 0
            foreach y in 2017 2018 2019 2020 2021 2023 2024 {
                replace coef = _b[es`y'] if year == `y'
                replace se = _se[es`y'] if year == `y'
            }
            export delimited using "stata/part2_event_study.csv", replace
            generate double lo = coef - 1.96 * se
            generate double hi = coef + 1.96 * se
            twoway (rcap lo hi year, lcolor(gs10)) (connected coef year), yline(0) xline(2022.5, lpattern(dash)) ///
                legend(off) xtitle("") ytitle("Coefficient (log points per SD of access)") ///
                title("Model 2 event study, base year 2022")
            graph export "stata/part2_event_study.png", replace width(1600)
        restore
    }
}

* Why the outcome is all cyber crimes against women: the "other" category (national totals)
*   Expected: cyber share of all crimes against women 1.18% (2017), 3.24% (2022), 4.35% (2023),
*   4.22% (2024); "other" share of cyber crimes against women 64.9% (2021), 75.2% (2024);
*   2023-24 vs 2021-22: "other" +68%, the five named types together +18%.
preserve
    use "stata/national_year.dta", clear
    keep if inrange(year, 2017, 2024)
    generate double cyber_share_pct = 100 * cyber_vaw_cases / women_total_cases
    generate double other_share_pct = 100 * cyber_vaw_other / cyber_vaw_cases
    generate double named = cyber_vaw_cases - cyber_vaw_other
    format cyber_share_pct other_share_pct %6.2f
    list year cyber_vaw_cases women_total_cases cyber_share_pct cyber_vaw_other other_share_pct named, noobs sep(0)
    quietly summarize cyber_vaw_other if inrange(year, 2021, 2022)
    local o0 = r(mean)
    quietly summarize cyber_vaw_other if inrange(year, 2023, 2024)
    local o1 = r(mean)
    quietly summarize named if inrange(year, 2021, 2022)
    local n0 = r(mean)
    quietly summarize named if inrange(year, 2023, 2024)
    local n1 = r(mean)
    display "2023-24 vs 2021-22: other x" %5.2f `o1'/`o0' ", named types x" %5.2f `n1'/`n0'
restore

* By crime type: each cyber head against offline crimes (NFHS-5 access)
*   includes "other" by itself (expected 1.22, p = 0.46)
display _n "--- Model 2 by crime type"
use "stata/state_category_year_panel.dta", clear
keep if inlist(category_group, "cyber_women", "offline_women") & !missing(access_nfhs5_15to49_avg)
tempfile heads
save `heads'
levelsof category if category_group == "cyber_women", local(cyberheads)
foreach h of local cyberheads {
    use `heads', clear
    keep if category == "`h'" | category_group == "offline_women"
    generate ai = category_group == "cyber_women"
    generate post = year >= 2023
    makefe
    zstate access_nfhs5_15to49_avg
    generate double treat = ai * post * z
    display _n "--- head: `h'"
    ppmlhdfe cases treat, absorb(sc st ct) vce(cluster sid)
    display "Rate ratio: " %6.3f exp(_b[treat])
}

* Placebo: cyber fraud as the treated category (expected 0.71, p = 0.30)
use "stata/state_category_year_panel.dta", clear
keep if inlist(category_group, "cyber_placebo", "offline_women")
generate ai = category_group == "cyber_placebo"
generate post = year >= 2023
makefe
keep if !missing(access_nfhs5_15to49_avg)
zstate access_nfhs5_15to49_avg
generate double treat = ai * post * z
display _n "--- Model 2 placebo: cyber fraud"
ppmlhdfe cases treat, absorb(sc st ct) vce(cluster sid)

* Fake shock years, 2017-2022 only (expected 1.06-1.10, all p > 0.16)
foreach fy in 2019 2020 2021 {
    use `m2', clear
    keep if !missing(access_nfhs5_15to49_avg) & year <= 2022
    zstate access_nfhs5_15to49_avg
    generate double treat = ai * (year >= `fy') * z
    display _n "--- Model 2 fake shock year `fy'"
    ppmlhdfe cases treat, absorb(sc st ct) vce(cluster sid)
}

* Robustness (expected 1.05-1.08)
foreach r in drop2020 drop2024 dropKATG {
    use `m2', clear
    keep if !missing(access_nfhs5_15to49_avg)
    if "`r'" == "drop2020" drop if year == 2020
    if "`r'" == "drop2024" drop if year == 2024
    if "`r'" == "dropKATG" drop if inlist(state, "Karnataka", "Telangana")
    zstate access_nfhs5_15to49_avg
    generate double treat = ai * post * z
    display _n "--- Model 2 robustness: `r'"
    ppmlhdfe cases treat, absorb(sc st ct) vce(cluster sid)
}

* =============================================================================
* 2b  LABELLING CONTROLS
*   Break = State-year where the IT Act share of cyber cases or the 'other' share of cyber
*   crimes against women jumps by more than 30 points (stata/labelling_breaks.dta); 17 States.
*   Expected (Python): drop break States 1.43 (p = 0.035); regime FE 1.11 (0.61);
*   'other' share 1.04 (0.85); all controls 1.02 (0.92).
*   Stable vs unstable (NFHS-5): stable 1.54 (p = 0.031), unstable 0.85 (0.47), difference p = 0.048.
* =============================================================================
display _n "==================== 2b LABELLING CONTROLS ===================="
use `m2', clear
merge m:1 state year using "stata/labelling_breaks.dta", keep(master match) nogenerate
replace regime = 0 if missing(regime)
bysort state: egen breakstate = max(label_break)
replace breakstate = 0 if missing(breakstate)
foreach v in other_share it_share {
    quietly summarize `v'
    replace `v' = r(mean) if missing(`v')
}
generate double cyb_other = ai * other_share
generate double cyb_it = ai * it_share
egen scr = group(state category regime)
keep if !missing(access_nfhs5_15to49_avg)
tempfile lab2
save `lab2'

display _n "--- Drop the 17 States with labelling breaks"
keep if breakstate == 0
zstate access_nfhs5_15to49_avg
generate double treat = ai * post * z
ppmlhdfe cases treat, absorb(sc st ct) vce(cluster sid)
display "Rate ratio: " %6.3f exp(_b[treat])

display _n "--- Same 18 States: event study"
foreach y in 2017 2018 2019 2020 2021 2023 2024 {
    generate double es`y' = ai * z * (year == `y')
}
ppmlhdfe cases es2017 es2018 es2019 es2020 es2021 es2023 es2024, absorb(sc st ct) vce(cluster sid)
test es2017 es2018 es2019 es2020 es2021

use `lab2', clear
zstate access_nfhs5_15to49_avg
generate double treat = ai * post * z
display _n "--- State x category x recording-regime fixed effects"
ppmlhdfe cases treat, absorb(scr st ct) vce(cluster sid)
display _n "--- Control for the 'other' share"
ppmlhdfe cases treat cyb_other, absorb(sc st ct) vce(cluster sid)
display _n "--- Regime FE + 'other' and IT Act shares"
ppmlhdfe cases treat cyb_other cyb_it, absorb(scr st ct) vce(cluster sid)

* All 35 States, effect allowed to differ by recording stability
* (stable States also get their own post-2022 shift)
foreach x in access_nfhs5_15to49_avg access_cams2023_15plus {
    use `lab2', clear
    keep if !missing(`x')
    zstate `x'
    generate stable = breakstate == 0
    generate double treat_stable = ai * post * z * stable
    generate double treat_unstable = ai * post * z * (1 - stable)
    generate double post_stable = ai * post * stable
    display _n "--- Stable vs unstable States, exposure: `x'"
    ppmlhdfe cases treat_stable treat_unstable post_stable, absorb(sc st ct) vce(cluster sid)
    display "Stable: " %6.3f exp(_b[treat_stable]) "   Unstable: " %6.3f exp(_b[treat_unstable])
    test treat_stable = treat_unstable
}

* ---------------------------------------------------------------- optional: randomisation inference
* Permutes exposure across States (needs: ssc install ritest). Slow: about 300 PPML fits.
* use `m2', clear
* keep if !missing(access_nfhs5_15to49_avg)
* zstate access_nfhs5_15to49_avg
* ritest z _b[c.ai#c.post#c.z], reps(300) seed(1) cluster(sid): ///
*     ppmlhdfe cases c.ai#c.post#c.z, absorb(sc st ct) vce(cluster sid)

log close
