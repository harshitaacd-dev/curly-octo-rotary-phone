* =============================================================================
* setup.do  --  shared setup for part1.do, part2.do and part3.do
*   Finds the repository root, installs the packages, and defines four helper programs:
*     zas       standardise a State-level variable across States (mean 0, SD 1)
*     build_m   State x crime x year panel: cyber crimes against women (summed) + offline crimes
*     merge_ctl add income, urban share and police capacity, in logs
*     fe_ids    fixed-effect identifiers
*     savetab   save the models stored with eststo as a table (Word .rtf and .csv) in stata/tables/
* Each part file runs this first:  run stata/setup.do
* =============================================================================

version 16
set more off

* Repository root on this computer; every path below is relative to it.
capture cd "/Users/Academic/Downloads/curly-octo-rotary-phone-claude-stata"

* If that folder is not found, fall back: use the current folder, or step up one level from stata/.
capture confirm file "stata/state_year_panel.dta"
if _rc {
    capture confirm file "state_year_panel.dta"
    if !_rc cd ..
    else {
        display as error "Cannot find the stata folder: cd to the folder that contains it, then run again"
        exit 601
    }
}

foreach p in ftools reghdfe ppmlhdfe estout {
    capture which `p'
    if _rc ssc install `p', replace
}

capture mkdir "stata/tables"

* zas x newname: standardise State-level variable x across the States in memory
capture program drop zas
program define zas
    args x newname
    capture drop `newname'
    tempvar tag
    egen `tag' = tag(state) if !missing(`x')
    quietly summarize `x' if `tag' == 1
    generate double `newname' = (`x' - r(mean)) / r(sd)
end

* build_m [, placebo]: one category for all cyber crimes against women (or cyber fraud with
* placebo) plus the five offline crimes against women; cyber = 1 for the treated category
capture program drop build_m
program define build_m
    syntax [, placebo]
    local tg = cond("`placebo'" == "", "cyber_women", "cyber_placebo")
    use "stata/state_category_year_panel.dta", clear
    keep if inlist(category_group, "`tg'", "offline_women")
    replace category = "treated" if category_group == "`tg'"
    collapse (sum) cases (first) access_cams2023_15plus access_nss2017_5plus access_nfhs5_15to49_avg ///
        access_cams2023_15to24 ads_nudify_to_genai_post ads_nudify_per_lakh_post ///
        trends_deepfake_awareness_pre trends_face_swap_pre, by(state year category category_group)
    generate cyber = category_group == "`tg'"
    generate post = year >= 2023
end

* merge_ctl: income (log per capita NSDP, RBI), urban share (CAMS), civil police per lakh 2020
* (log) and cyber police stations + cells per crore 2024 (log of 1 + x)
capture program drop merge_ctl
program define merge_ctl
    merge m:1 state using "stata/state_controls.dta", keep(master match) nogenerate
    merge m:1 state using "stata/state_police.dta", keep(master match) nogenerate
    generate double ln_income = ln(nsdp_pc_avg)
    generate double ln_police = ln(civil_police_per_lakh_2020)
    generate double ln_cyber_units = ln(1 + cyber_units_per_crore)
end

* fe_ids: State x category, State x year, category x year, State
capture program drop fe_ids
program define fe_ids
    capture drop sc st ct sid
    egen sc = group(state category)
    egen st = group(state year)
    egen ct = group(category year)
    egen sid = group(state)
end

* savetab name "title": rate ratios with p-values in parentheses, one column per stored model
capture program drop savetab
program define savetab
    args name title
    local opts eform b(3) p(3) star(* 0.10 ** 0.05 *** 0.01) drop(_cons, relax) mtitles nonumbers ///
        stats(N, labels("Observations") fmt(0)) ///
        addnotes("Rate ratios (exp of coefficients); p-values in parentheses; SE clustered by State unless stated.")
    esttab using "stata/tables/`name'.rtf", replace title("`title'") `opts'
    esttab using "stata/tables/`name'.csv", replace title("`title'") `opts'
    esttab, title("`title'") `opts'
    eststo clear
end
