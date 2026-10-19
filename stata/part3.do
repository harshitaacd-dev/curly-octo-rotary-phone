* =============================================================================
* part3.do  --  Part 3: crimes against women in NCRB versus online reporting
*
*   3a  Year by year, 2021-2025: complaints to platforms and police-recorded cases (NCRB)
*   3b  Growth index (2022 = 100): how fast each source grew
*   3c  Every platform: sexual-content complaints as a share of its complaints
*   3d  Reporting chain, 2023 to 2024: each stage's change
*
* Run from the repository root:   do stata/part3.do
* Output: stata/part3_results.txt (log), stata/part3_yearly.png, stata/part3_growth.png,
*         stata/part3_chain.png
*
* Platform figures are complaints received under India's IT Rules 2021 (monthly reports).
* Categories differ by platform:
*   Facebook, Instagram  "Content showing me in nudity/partial nudity or in a sexual act"
*   X                    sensitive adult content; synthetic or manipulated media
*   Google (incl. YouTube) graphic sexual content
*   Snapchat             reports of sexual content
*   ShareChat, Moj       sexually explicit content (June 2021 - October 2022 only)
* Cautions: 2021 covers June-December for most platforms; X changed its report format in March
* 2025 (category counts fall to about zero); NCRB ends in 2024.
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
log using "stata/part3_results.txt", text replace

* =============================================================================
* 3a  YEAR BY YEAR: platform complaints and NCRB cases
*   platform_complaints = sexual-content complaints to X (incl. synthetic media), Facebook,
*   Instagram and Google: the platforms that report complaints (not user reports) every year.
*   Snapchat, ShareChat and Moj count user reports of content, a much larger and different
*   measure, so they are listed separately.
*   Expected: platform complaints 1,981 (2022), 24,997 (2023), 51,763 (2024);
*   per NCRB case 0.14, 1.28, 2.78.
* =============================================================================
display _n "==================== 3a YEAR BY YEAR ===================="
use "stata/national_year.dta", clear
keep if inrange(year, 2021, 2025)
egen double platform_complaints = rowtotal(x_sexual x_synthetic meta_sexual google_sexual), missing
generate double complaints_per_ncrb_case = platform_complaints / cyber_vaw_cases
format platform_complaints cyber_vaw_cases cyber_vaw_obscene_material snap_sexual sharechat_sexual ///
    moj_sexual x_all meta_all %12.0fc
format complaints_per_ncrb_case meta_sexual_share_pct %6.2f

display _n "Months covered by each platform's reports"
list year x_months meta_months google_months snap_months sharechat_months moj_months, noobs sep(0)

display _n "Police-recorded (NCRB) and complaints to platforms"
list year cyber_vaw_cases cyber_vaw_obscene_material platform_complaints complaints_per_ncrb_case, noobs sep(0)

display _n "Complaints by platform (sexual content)"
list year x_sexual x_synthetic meta_sexual google_sexual, noobs sep(0)

display _n "User reports of sexual content (Snapchat, ShareChat, Moj)"
list year snap_sexual sharechat_sexual moj_sexual, noobs sep(0)

display _n "All complaints to X and Meta, and Meta's intimate-image share"
list year x_all meta_all meta_sexual meta_sexual_share_pct, noobs sep(0)

display _n "News-reported incidents of image-based abuse"
list year news_all_incidents, noobs sep(0)

preserve
    keep if inrange(year, 2022, 2024)
    twoway (connected platform_complaints year) (connected cyber_vaw_cases year), ///
        yscale(log) ylabel(1000 5000 20000 50000, format(%9.0fc)) xlabel(2022(1)2024) ///
        ytitle("Number (log scale)") xtitle("") ///
        legend(order(1 "Complaints to platforms: sexual content" 2 "NCRB cyber crimes against women") cols(1)) ///
        title("Complaints to platforms and police records, India")
    graph export "stata/part3_yearly.png", replace width(1800)
restore

* =============================================================================
* 3b  GROWTH INDEX, 2022 = 100
*   Each series divided by its own 2022 value: compares how fast each source grew,
*   whatever its size. Expected 2023, 2024: NCRB cyber crimes against women 135, 129;
*   obscene material 123, 112; platform complaints 1262, 2613; Meta intimate images 1981, 2263;
*   Snapchat 137, 165; all complaints to Meta 729, 1021 (the complaint route itself grew).
* =============================================================================
display _n "==================== 3b GROWTH INDEX (2022 = 100) ===================="
keep if inrange(year, 2022, 2024)
foreach v in cyber_vaw_cases cyber_vaw_obscene_material platform_complaints meta_sexual x_sexual ///
             snap_sexual meta_all x_all {
    quietly summarize `v' if year == 2022
    generate double idx_`v' = 100 * `v' / r(mean)
}
format idx_* %8.0f
list year idx_cyber_vaw_cases idx_cyber_vaw_obscene_material idx_platform_complaints, noobs sep(0)
list year idx_meta_sexual idx_x_sexual idx_snap_sexual idx_meta_all idx_x_all, noobs sep(0)

twoway (connected idx_platform_complaints year) (connected idx_snap_sexual year) ///
    (connected idx_cyber_vaw_cases year), yscale(log) ylabel(100 200 500 1000 2500) xlabel(2022(1)2024) ///
    ytitle("Index, 2022 = 100 (log scale)") xtitle("") ///
    legend(order(1 "Complaints to X, Facebook, Instagram, Google" 2 "Snapchat user reports" ///
    3 "NCRB cyber crimes against women") cols(1)) ///
    title("Growth of online reporting and police records")
graph export "stata/part3_growth.png", replace width(1800)

* =============================================================================
* 3c  EVERY PLATFORM: sexual-content complaints as % of the platform's complaints
*   Compare each platform with itself over time, not across platforms (categories differ).
*   Months without a complete breakdown (ShareChat and Moj, November 2021) are dropped;
*   X stops at February 2025. Snapchat November 2025 dropped (duplicated report).
*   Expected (%), 2021-2025: Facebook 5.9 5.2 3.2 4.9 5.6; Instagram 7.9 1.7 9.3 4.9 2.8;
*   Snapchat 41.0 26.8 19.3 20.3 22.5; X 9.2 6.8 7.4 14.4 44.1 (2025 = Jan-Feb); Google ~0;
*   ShareChat 7.2 8.5; Moj 12.0 9.2 (2021-22 only).
* =============================================================================
display _n "==================== 3c EVERY PLATFORM ===================="
use "stata/platform_month_panel.dta", clear
drop if suspect_duplicate == 1
drop if platform == "X" & month >= "2025-03"
bysort platform month: egen has_other = max(category_group == "placebo")
keep if has_other
generate year = real(substr(month, 1, 4))
generate double target = count * inlist(category_group, "sexual", "synthetic")
collapse (sum) target count, by(platform year)
generate double share_pct = 100 * target / count
display _n "Sexual-content complaints, % of each platform's complaints, by year"
tabdisp platform year if year <= 2025, cell(share_pct) format(%5.1f)
display _n "Complaints received, all categories, by year"
tabdisp platform year if year <= 2025, cell(count) format(%12.0fc)

* =============================================================================
* 3d  REPORTING CHAIN, 2023 to 2024
*   Each stage's 2024 level as a multiple of its 2023 level. The national cyber crime
*   reporting portal publishes no category breakdown (missing stage).
* =============================================================================
display _n "==================== 3d REPORTING CHAIN ===================="
use "stata/funnel_2023_2024.dta", clear
drop if strpos(stage, "Searches")
generate order = _n
list stage source y2023 y2024 ratio_2024_to_2023, noobs sep(0) abbreviate(20)
generate double log2_ratio = ln(ratio_2024_to_2023) / ln(2)
graph hbar log2_ratio if kind != "missing", over(stage, sort(order) label(labsize(vsmall))) ///
    ytitle("Change 2023 to 2024, doublings (0 = no change, 1 = 2x, -1 = half)") ///
    title("Complaints to platforms and police records, 2023 to 2024") bar(1, color(navy))
graph export "stata/part3_chain.png", replace width(1800)

log close
