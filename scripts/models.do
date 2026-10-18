* =============================================================================
* models.do  --  Stata replication of scripts/estimate_models.py
*
* Models 1 and 2 of research/econometric-specification.md:
*   Poisson PPML with fixed effects State x category, State x year, category x year,
*   standard errors clustered by State. Exposure standardised across States
*   (mean 0, SD 1) within each estimation sample, so exp(b) = rate ratio per SD.
*
* Run from the repository root:
*     cd "path/to/curly-octo-rotary-phone"
*     do scripts/models.do
*
* Needs (once):  ssc install ftools ; ssc install reghdfe ; ssc install ppmlhdfe
* Optional RI:   ssc install ritest
* Results are written to analysis/models/stata_results.txt (log) and
* analysis/models/stata_*.csv (event studies).
* =============================================================================

version 16
clear all
set more off
capture log close
log using "analysis/models/stata_results.txt", text replace

foreach p in ftools reghdfe ppmlhdfe {
    capture which `p'
    if _rc ssc install `p', replace
}

* ---------------------------------------------------------------- load panel
import delimited "data/analysis/state_category_year_panel.csv", clear varnames(1) encoding(utf8)
keep state year category category_group cases is_cyber_vaw is_ai_susceptible ///
     access_cams2023_15plus access_nss2017_5plus access_nfhs5_15to49_avg access_cams2023_15to24 ///
     ads_nudify_to_genai_post ads_nudify_per_lakh_post trends_deepfake_awareness_pre trends_face_swap_pre
tempfile panel
save `panel'

* Standardise a State-level exposure within the current sample (one value per State)
capture program drop zstate
program define zstate
    args x
    capture drop z _tag
    egen _tag = tag(state)
    quietly summarize `x' if _tag
    generate double z = (`x' - r(mean)) / r(sd)
    drop _tag
end

* Fixed-effect identifiers
capture program drop makefe
program define makefe
    capture drop sc st ct
    egen sc = group(state category)
    egen st = group(state year)
    egen ct = group(category year)
end

* =============================================================================
* MODEL 1: internet access and the growth of cyber crime against women, 2017-2024
*   Outcome: all cyber crimes against women summed into one category,
*   compared with five offline crimes against women.
* =============================================================================
use `panel', clear
keep if inlist(category_group, "cyber_women", "offline_women")
replace category = "cyber crimes against women (all)" if category_group == "cyber_women"
collapse (sum) cases (first) access_* ads_* trends_*, by(state year category category_group)
generate cyber = category_group == "cyber_women"
makefe
tempfile m1
save `m1'

display _n "==================== MODEL 1: by access measure ===================="
foreach x in access_cams2023_15plus access_nss2017_5plus access_nfhs5_15to49_avg access_cams2023_15to24 {
    use `m1', clear
    keep if !missing(`x')
    zstate `x'
    generate double treat = cyber * z * (year - 2017)
    display _n "--- Model 1, exposure: `x'"
    ppmlhdfe cases treat, absorb(sc st ct) vce(cluster state)
    display "Rate ratio per SD per year: " %6.3f exp(_b[treat])
}

* Event study, base year 2017 (main exposure)
use `m1', clear
keep if !missing(access_cams2023_15plus)
zstate access_cams2023_15plus
forvalues y = 2018/2024 {
    generate double es`y' = cyber * z * (year == `y')
}
display _n "--- Model 1 event study (base 2017)"
ppmlhdfe cases es2018-es2024, absorb(sc st ct) vce(cluster state)
preserve
    clear
    set obs 8
    generate year = 2016 + _n
    generate double coef = 0
    generate double se = 0
    forvalues y = 2018/2024 {
        replace coef = _b[es`y'] if year == `y'
        replace se = _se[es`y'] if year == `y'
    }
    export delimited using "analysis/models/stata_model1_event_study.csv", replace
restore

* Placebo: cyber fraud instead of cyber crime against women
use `panel', clear
keep if inlist(category_group, "cyber_placebo", "offline_women")
generate cyber = category_group == "cyber_placebo"
makefe
keep if !missing(access_cams2023_15plus)
zstate access_cams2023_15plus
generate double treat = cyber * z * (year - 2017)
display _n "--- Model 1 placebo: cyber fraud"
ppmlhdfe cases treat, absorb(sc st ct) vce(cluster state)

* Robustness on the main exposure
foreach r in drop2020 drop2024 dropKATG {
    use `m1', clear
    keep if !missing(access_cams2023_15plus)
    if "`r'" == "drop2020" drop if year == 2020
    if "`r'" == "drop2024" drop if year == 2024
    if "`r'" == "dropKATG" drop if inlist(state, "Karnataka", "Telangana")
    zstate access_cams2023_15plus
    generate double treat = cyber * z * (year - 2017)
    display _n "--- Model 1 robustness: `r'"
    ppmlhdfe cases treat, absorb(sc st ct) vce(cluster state)
}

* =============================================================================
* MODEL 2: the generative-AI boom (Post = 2023-2024)
*   Treated: all cyber crimes against women summed into one category (as in Model 1).
*   Comparison: offline crimes against women.
* =============================================================================
use `m1', clear
generate ai = cyber
generate post = year >= 2023
tempfile m2
save `m2'

display _n "==================== MODEL 2: by exposure measure ===================="
foreach x in access_nfhs5_15to49_avg access_cams2023_15plus ads_nudify_to_genai_post ///
             ads_nudify_per_lakh_post trends_deepfake_awareness_pre trends_face_swap_pre {
    use `m2', clear
    keep if !missing(`x')
    zstate `x'
    generate double treat = ai * post * z
    display _n "--- Model 2, exposure: `x'"
    ppmlhdfe cases treat, absorb(sc st ct) vce(cluster state)
    display "Rate ratio per SD after 2022: " %6.3f exp(_b[treat])
}

* Event study, base year 2022, with joint pre-trend test
foreach x in access_nfhs5_15to49_avg ads_nudify_to_genai_post {
    use `m2', clear
    keep if !missing(`x')
    zstate `x'
    foreach y in 2017 2018 2019 2020 2021 2023 2024 {
        generate double es`y' = ai * z * (year == `y')
    }
    display _n "--- Model 2 event study (base 2022), exposure: `x'"
    ppmlhdfe cases es2017 es2018 es2019 es2020 es2021 es2023 es2024, absorb(sc st ct) vce(cluster state)
    display "Joint pre-trend test (2017-2021 = 0):"
    test es2017 es2018 es2019 es2020 es2021
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
        export delimited using "analysis/models/stata_model2_event_study_`x'.csv", replace
    restore
}

* Placebo: cyber fraud as the treated category
use `panel', clear
keep if inlist(category_group, "cyber_placebo", "offline_women")
generate ai = category_group == "cyber_placebo"
generate post = year >= 2023
makefe
keep if !missing(access_nfhs5_15to49_avg)
zstate access_nfhs5_15to49_avg
generate double treat = ai * post * z
display _n "--- Model 2 placebo: cyber fraud"
ppmlhdfe cases treat, absorb(sc st ct) vce(cluster state)

* Fake shock years, 2017-2022 only
foreach fy in 2019 2020 2021 {
    use `m2', clear
    keep if !missing(access_nfhs5_15to49_avg) & year <= 2022
    zstate access_nfhs5_15to49_avg
    generate double treat = ai * (year >= `fy') * z
    display _n "--- Model 2 fake shock year `fy'"
    ppmlhdfe cases treat, absorb(sc st ct) vce(cluster state)
}

* Robustness
foreach r in drop2020 drop2024 dropKATG {
    use `m2', clear
    keep if !missing(access_nfhs5_15to49_avg)
    if "`r'" == "drop2020" drop if year == 2020
    if "`r'" == "drop2024" drop if year == 2024
    if "`r'" == "dropKATG" drop if inlist(state, "Karnataka", "Telangana")
    zstate access_nfhs5_15to49_avg
    generate double treat = ai * post * z
    display _n "--- Model 2 robustness: `r'"
    ppmlhdfe cases treat, absorb(sc st ct) vce(cluster state)
}

* ---------------------------------------------------------------- optional: randomisation inference
* Uncomment to permute exposure across States (needs: ssc install ritest). Slow: about 300 PPML fits.
* use `m2', clear
* keep if !missing(ads_nudify_to_genai_post)
* zstate ads_nudify_to_genai_post
* generate double treat = ai * post * z
* ritest z _b[treat], reps(300) seed(1) cluster(state): ///
*     ppmlhdfe cases c.ai#c.post#c.z, absorb(sc st ct) vce(cluster state)

log close
