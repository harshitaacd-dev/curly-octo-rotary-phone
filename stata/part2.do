* =============================================================================
* part2.do  --  Part 2: the period after AI image tools spread (Model 2)
*   Follows the Methodology, Part 2:
*     A  Why the outcome is all cyber crimes against women: the "other" category
*     B  Model 2 for each exposure measure
*     C  Validity: event study and pre-trend test, fake start years, placebo, dropping years/States
*     D  Each cyber crime type, including "other" alone
*     E  Controlling for labelling
*     F  Controlling for capacity: income, urban share, civil police, cyber police units
*     G  Expanding cyber policing within States, 2020-2024
* Run from the repository root:   do stata/part2.do
* Output: stata/part2_results.txt; tables and figures in stata/tables/ (part2_*)
* =============================================================================

run stata/setup.do
capture log close
log using "stata/part2_results.txt", text replace

* =============================================================================
* A  THE "OTHER" CATEGORY (national totals)
*   Expected: cyber share of all crimes against women 1.18% (2017), 3.24% (2022), 4.35% (2023),
*   4.22% (2024); "other" share of cyber crimes against women 64.9% (2021), 75.2% (2024);
*   2023-24 vs 2021-22: "other" x1.68, the named types together x1.18
* =============================================================================
display _n "==================== A: THE OTHER CATEGORY ===================="
use "stata/national_year.dta", clear
keep if inrange(year, 2017, 2024)
generate double cyber_share_pct = 100 * cyber_vaw_cases / women_total_cases
generate double other_share_pct = 100 * cyber_vaw_other / cyber_vaw_cases
generate double named = cyber_vaw_cases - cyber_vaw_other
format cyber_share_pct other_share_pct %6.2f
list year cyber_vaw_cases women_total_cases cyber_share_pct cyber_vaw_other other_share_pct named, noobs sep(0)
export delimited year cyber_vaw_cases women_total_cases cyber_share_pct cyber_vaw_other other_share_pct named ///
    using "stata/tables/part2_table1_other_category.csv", replace
twoway (connected cyber_share_pct year, yaxis(1)) (connected other_share_pct year, yaxis(2)), ///
    xline(2022.5, lpattern(dash)) xtitle("") ytitle("Cyber crime, % of all crimes against women", axis(1)) ///
    ytitle("Other category, % of cyber crimes against women", axis(2)) ///
    legend(order(1 "Cyber share of crimes against women" 2 "Other category share of cyber crimes against women") cols(1)) ///
    title("Cyber crime against women and the other category, India")
graph export "stata/tables/part2_figure1_other_category.png", replace width(1600)
foreach v in cyber_vaw_other named {
    quietly summarize `v' if inrange(year, 2021, 2022)
    local before = r(mean)
    quietly summarize `v' if inrange(year, 2023, 2024)
    display "`v': 2023-24 vs 2021-22 = x" %5.2f r(mean) / `before'
}

* =============================================================================
* B  MODEL 2
*   cases = exp(b x Cyber x Post x Exposure + State x crime + State x year + crime x year)
*   Post = 2023-2024. Main exposure: NFHS-5 internet access (2019-21), measured before the period.
*   Expected: NFHS-5 1.07 (p = 0.72); CAMS 0.86 (0.35); nudify-to-AI search ratio 0.99 (0.98);
*   nudify searches per lakh 1.00 (0.98); Trends deepfake awareness 1.13 (0.57); Trends face swap
*   0.74 (<0.001, implausibly small SE)
* =============================================================================
display _n "==================== B: MODEL 2 ===================="
build_m
fe_ids
tempfile m2
save `m2'

foreach x in access_nfhs5_15to49_avg access_cams2023_15plus ads_nudify_to_genai_post ///
             ads_nudify_per_lakh_post trends_deepfake_awareness_pre trends_face_swap_pre {
    use `m2', clear
    keep if !missing(`x')
    zas `x' z
    generate double treat = cyber * post * z
    display _n "--- Model 2, exposure: `x'"
    eststo, title("`x'"): ppmlhdfe cases treat, absorb(sc st ct) vce(cluster sid)
    display "Rate ratio per SD after 2022: " %6.3f exp(_b[treat])
}
savetab part2_table2_model2 "Part 2, Model 2: change after 2022 per SD of exposure"

* =============================================================================
* C  VALIDITY
* =============================================================================
display _n "==================== C: VALIDITY ===================="

* C1 Event study, base year 2022, joint pre-trend test. Expected: years 2017-2024 between -0.08 and
*    +0.06; joint pre-trend p = 0.74 (NFHS-5). The nudify ratio fails (p < 0.001).
foreach x in access_nfhs5_15to49_avg ads_nudify_to_genai_post {
    use `m2', clear
    keep if !missing(`x')
    zas `x' z
    foreach y in 2017 2018 2019 2020 2021 2023 2024 {
        generate double es`y' = cyber * z * (year == `y')
    }
    display _n "--- Event study, exposure: `x'"
    ppmlhdfe cases es2017 es2018 es2019 es2020 es2021 es2023 es2024, absorb(sc st ct) vce(cluster sid)
    test es2017 es2018 es2019 es2020 es2021
    estadd scalar pretrend_p = r(p)
    eststo, title("`x'")
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
            export delimited using "stata/tables/part2_table3_event_study_coefs.csv", replace
            generate double lo = coef - 1.96 * se
            generate double hi = coef + 1.96 * se
            twoway (rcap lo hi year, lcolor(gs10)) (connected coef year), yline(0) xline(2022.5, lpattern(dash)) ///
                legend(off) xtitle("") ytitle("Coefficient (log points per SD of access)") ///
                title("Model 2 event study, base year 2022")
            graph export "stata/tables/part2_figure2_event_study.png", replace width(1600)
        restore
    }
}
esttab using "stata/tables/part2_table3_event_study.rtf", replace eform b(3) p(3) star(* 0.10 ** 0.05 *** 0.01) ///
    mtitles nonumbers stats(pretrend_p N, labels("Joint pre-trend test, p" "Observations") fmt(3 0)) ///
    title("Part 2, event study (base 2022): rate ratio by year per SD of exposure")
esttab using "stata/tables/part2_table3_event_study.csv", replace eform b(3) p(3) mtitles nonumbers ///
    stats(pretrend_p N, labels("Joint pre-trend test, p" "Observations") fmt(3 0))
eststo clear

* C2 Fake start years, 2017-2022 only. Expected 1.06-1.10, all p > 0.16
foreach fy in 2019 2020 2021 {
    use `m2', clear
    keep if !missing(access_nfhs5_15to49_avg) & year <= 2022
    zas access_nfhs5_15to49_avg z
    generate double treat = cyber * (year >= `fy') * z
    display _n "--- Fake start year `fy'"
    eststo, title("Fake start `fy'"): ppmlhdfe cases treat, absorb(sc st ct) vce(cluster sid)
}

* C3 Placebo: cyber fraud. Expected 0.71 (p = 0.30)
build_m, placebo
fe_ids
keep if !missing(access_nfhs5_15to49_avg)
zas access_nfhs5_15to49_avg z
generate double treat = cyber * post * z
display _n "--- Placebo: cyber fraud"
eststo, title("Placebo: cyber fraud"): ppmlhdfe cases treat, absorb(sc st ct) vce(cluster sid)

* C4 Dropping years and States. Expected 1.05-1.08, p 0.73-0.76
foreach r in drop2020 drop2024 dropKATG {
    use `m2', clear
    keep if !missing(access_nfhs5_15to49_avg)
    if "`r'" == "drop2020" drop if year == 2020
    if "`r'" == "drop2024" drop if year == 2024
    if "`r'" == "dropKATG" drop if inlist(state, "Karnataka", "Telangana")
    zas access_nfhs5_15to49_avg z
    generate double treat = cyber * post * z
    display _n "--- Check: `r'"
    eststo, title("`r'"): ppmlhdfe cases treat, absorb(sc st ct) vce(cluster sid)
}
savetab part2_table4_validity "Part 2, validity checks (NFHS-5 exposure)"

* =============================================================================
* D  EACH CYBER CRIME TYPE against offline crimes (NFHS-5)
*   Expected: other 1.22 (0.46); obscene material 1.02 (0.88); blackmail 0.91 (0.76);
*   stalking 0.71 (0.17); fake profile 0.49 (0.41); morphing 0.18 (0.02, small counts)
* =============================================================================
display _n "==================== D: EACH TYPE ===================="
use "stata/state_category_year_panel.dta", clear
keep if inlist(category_group, "cyber_women", "offline_women") & !missing(access_nfhs5_15to49_avg)
tempfile heads
save `heads'
levelsof category if category_group == "cyber_women", local(types)
foreach h of local types {
    use `heads', clear
    keep if category == "`h'" | category_group == "offline_women"
    generate cyber = category_group == "cyber_women"
    generate post = year >= 2023
    fe_ids
    zas access_nfhs5_15to49_avg z
    generate double treat = cyber * post * z
    display _n "--- Type: `h'"
    eststo, title("`h'"): ppmlhdfe cases treat, absorb(sc st ct) vce(cluster sid)
    display "Rate ratio: " %6.3f exp(_b[treat])
}
savetab part2_table5_types "Part 2, Model 2 by cyber crime type (NFHS-5 exposure)"

* =============================================================================
* E  CONTROLLING FOR LABELLING
*   Break = the IT Act share of cyber cases or the "other" share of cyber crimes against women
*   jumps by more than 30 points (years with at least 20 cases); 17 of 35 States.
*   Expected: (a) drop break States 1.43 (p = 0.035); (b) regime fixed effects 1.11 (0.61);
*   (c) "other" share control 1.04 (0.85); regime FE + both shares 1.02 (0.92);
*   (d) stable 1.54 (0.031) vs unstable 0.85 (0.47), difference p = 0.048 (CAMS: 0.82 vs 0.90, p = 0.73)
* =============================================================================
display _n "==================== E: LABELLING ===================="
use `m2', clear
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
tempfile lab
save `lab'

use `lab', clear
keep if breakstate == 0 & !missing(access_nfhs5_15to49_avg)
zas access_nfhs5_15to49_avg z
generate double treat = cyber * post * z
display _n "--- (a) Without the 17 States with breaks"
eststo, title("(a) Stable States only"): ppmlhdfe cases treat, absorb(sc st ct) vce(cluster sid)

use `lab', clear
keep if !missing(access_nfhs5_15to49_avg)
zas access_nfhs5_15to49_avg z
generate double treat = cyber * post * z
display _n "--- (b) Separate baseline for each State's recording period"
eststo, title("(b) Period baselines"): ppmlhdfe cases treat, absorb(scr st ct) vce(cluster sid)
display _n "--- (c) Control for the other share"
eststo, title("(c) Other share"): ppmlhdfe cases treat cyb_other, absorb(sc st ct) vce(cluster sid)
display _n "--- (c) Recording-period baselines + other and IT Act shares"
eststo, title("(b)+(c) All"): ppmlhdfe cases treat cyb_other cyb_it, absorb(scr st ct) vce(cluster sid)

foreach x in access_nfhs5_15to49_avg access_cams2023_15plus {
    use `lab', clear
    keep if !missing(`x')
    zas `x' z
    generate stable = breakstate == 0
    generate double treat_stable = cyber * post * z * stable
    generate double treat_unstable = cyber * post * z * (1 - stable)
    generate double post_stable = cyber * post * stable
    display _n "--- (d) Stable vs unstable States, exposure: `x'"
    ppmlhdfe cases treat_stable treat_unstable post_stable, absorb(sc st ct) vce(cluster sid)
    test treat_stable = treat_unstable
    estadd scalar diff_p = r(p)
    eststo, title("(d) `x'")
}
esttab using "stata/tables/part2_table6_labelling.rtf", replace eform b(3) p(3) star(* 0.10 ** 0.05 *** 0.01) ///
    drop(_cons, relax) mtitles nonumbers stats(diff_p N, labels("Stable = unstable, p" "Observations") fmt(3 0)) ///
    title("Part 2, labelling controls (NFHS-5 exposure unless named)")
esttab using "stata/tables/part2_table6_labelling.csv", replace eform b(3) p(3) drop(_cons, relax) mtitles nonumbers ///
    stats(diff_p N, labels("Stable = unstable, p" "Observations") fmt(3 0))
esttab, eform b(3) p(3) drop(_cons, relax) mtitles nonumbers stats(diff_p N)
eststo clear

* =============================================================================
* F  CONTROLLING FOR CAPACITY (33 States with all controls)
*   Each control interacted the same way as exposure: Cyber x Post x Control.
*   Expected: income + urban: access 1.23 (0.25);
*   all four (income, urban, civil police 2020, cyber units): access 1.42 (0.042), police 0.58 (0.035),
*   income 0.95 (0.79), urban 1.04 (0.85), cyber units 1.02 (0.81). Exploratory: access and police
*   are correlated (0.56) and neither shows alone.
* =============================================================================
display _n "==================== F: CAPACITY CONTROLS ===================="
use `m2', clear
merge_ctl
keep if !missing(access_nfhs5_15to49_avg, ln_income, urban_share_cams, ln_police, ln_cyber_units)
zas access_nfhs5_15to49_avg z_access
zas ln_income z_income
zas urban_share_cams z_urban
zas ln_police z_police
zas ln_cyber_units z_cyber
foreach v in access income urban police cyber {
    generate double t_`v' = cyber * post * z_`v'
}
display _n "--- Model 2 + income and urban share"
eststo, title("+ income, urban"): ppmlhdfe cases t_access t_income t_urban, absorb(sc st ct) vce(cluster sid)
display _n "--- Model 2 + income, urban share, civil police and cyber police units"
eststo, title("+ police capacity"): ppmlhdfe cases t_access t_income t_urban t_police t_cyber, absorb(sc st ct) vce(cluster sid)
savetab part2_table7_capacity "Part 2, Model 2 with capacity controls (33 States; per SD after 2022)"

* =============================================================================
* G  EXPANDING CYBER POLICING WITHIN STATES, 2020-2024
*   cases = log(1 + cyber police stations and cells per crore) | State + year
*   (BPR&D reports for 1 January 2020, 2021, 2022, 2024; 2023 = average of 2022 and 2024)
*   Expected: cyber crime against women 0.83 (p = 0.068); offline 0.83 (0.13);
*   all cyber crime 0.90 (0.51); cyber fraud 1.63 (p = 0.027, 26 States)
* =============================================================================
display _n "==================== G: CYBER POLICING ===================="
use "stata/state_year_panel.dta", clear
merge 1:1 state year using "stata/state_police_year.dta", keep(match) nogenerate
egen sid = group(state)
generate double ln_units = ln(1 + cyber_units / (population_lakh / 100))
foreach y in cyber_vaw_cases offline_vaw_cases cyber_total_cases cyber_fraud {
    local off female_pop_lakh
    if inlist("`y'", "cyber_total_cases", "cyber_fraud") local off population_lakh
    display _n "--- Outcome: `y'"
    eststo, title("`y'"): ppmlhdfe `y' ln_units, absorb(sid year) exposure(`off') vce(cluster sid)
    display "Rate ratio: " %6.3f exp(_b[ln_units])
}
savetab part2_table8_cyber_policing "Part 2, cyber police stations and cells within States, 2020-2024"

* ---------------------------------------------------------------- optional: randomisation inference
* Shuffles exposure across States (ssc install ritest). Slow: 300 model fits. Expected RI p = 0.58.
* use `m2', clear
* keep if !missing(access_nfhs5_15to49_avg)
* zas access_nfhs5_15to49_avg z
* ritest z _b[c.cyber#c.post#c.z], reps(300) seed(1) cluster(sid): ///
*     ppmlhdfe cases c.cyber#c.post#c.z, absorb(sc st ct) vce(cluster sid)

log close
