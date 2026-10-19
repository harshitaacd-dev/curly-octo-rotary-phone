* =============================================================================
* part3.do  --  Part 3: crimes against women in NCRB versus online reporting
*
*   3a  Year by year, 2021-2025: complaints to platforms and police-recorded cases (NCRB)
*   3b  Growth index (2022 = 100): how fast each source grew
*   3c  Every platform: sexual-content complaints as a share of its complaints
*   3d  Reporting chain, 2023 to 2024: each stage's change
*   3e  MODEL. Main: share-adjusted growth, 2022-2024 (police: cyber vs offline crimes against women;
*       each platform: sexual-content vs its other complaints), with a z-test against police.
*       Secondary: raw growth of the counts, and a pooled five-platform summary.
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

* =============================================================================
* 3e  MODEL: growth of police records versus complaints to platforms, 2022-2024
*   MAIN (share-adjusted). Each side is measured against its own comparison group, so growth of
*   the complaint route itself is removed: complaints to Meta for every reason rose about 7x in
*   2023 with the amended IT Rules and the Grievance Appellate Committee.
*     Police:   cases = exp(b x Cyber x (year - 2022) + State x crime + State x year)
*               cyber crimes against women vs the five offline crimes; SE clustered by State
*     Platform: complaints = exp(t x Sexual x years since Jan 2022 + type + month)
*               sexual-content vs the platform's other complaints, monthly; robust SE
*     z = (t - b) / sqrt(se_t^2 + se_b^2): the two sources are independent.
*   Expected (Python): police 1.145 a year (1.04-1.27); Facebook 1.27 (p vs police 0.58),
*   Instagram 1.09 (0.85), X 1.49 (0.47), Snapchat 0.84 (<0.001), Google 0.97 (0.32).
*   SECONDARY (raw growth): police 1.13 a year; Facebook 3.74 (p < 0.001), Instagram 1.62 (0.34),
*   X 11.62 (p < 0.001), Snapchat 1.18 (0.49), Google 0.80 (0.013); pooled 2.96 (p = 0.040).
*   The pooled estimate is a rough summary of the platform side against police growth, not a
*   ranking or comparison between platforms.
* =============================================================================
display _n "==================== 3e MODEL: POLICE VS PLATFORM GROWTH ===================="

* ---- Police side, share-adjusted (cyber vs offline crimes against women)
use "stata/state_category_year_panel.dta", clear
keep if inlist(category_group, "cyber_women", "offline_women") & inrange(year, 2022, 2024)
replace category = "cyber crimes against women (all)" if category_group == "cyber_women"
collapse (sum) cases, by(state year category category_group)
generate cyber = category_group == "cyber_women"
generate double x = cyber * (year - 2022)
egen sc = group(state category)
egen st = group(state year)
egen sid = group(state)
display _n "--- Police, share-adjusted: cyber vs offline crimes against women"
ppmlhdfe cases x, absorb(sc st) vce(cluster sid)
scalar rb = _b[x]
scalar rsb = _se[x]
display "Police relative growth per year: " %6.3f exp(rb)

* ---- Police side, raw
use "stata/state_year_panel.dta", clear
keep if inrange(year, 2022, 2024) & !missing(cyber_vaw_cases)
generate t = year - 2022
egen sid = group(state)
display _n "--- Police, raw growth of cyber crimes against women"
ppmlhdfe cyber_vaw_cases t, absorb(sid) vce(cluster sid)
scalar nb = _b[t]
scalar nsb = _se[t]
display "Police raw growth per year: " %6.3f exp(nb)

* ---- Platform side, each platform
capture program drop platgrowth
program define platgrowth
    args plat
    use "stata/platform_month_panel.dta", clear
    drop if suspect_duplicate == 1
    keep if platform == "`plat'" & month >= "2022-01" & month <= "2024-12"
    generate target = inlist(category_group, "sexual", "synthetic")
    collapse (sum) count, by(month target)
    generate mdate = monthly(month, "YM")
    format mdate %tm
    generate double t = (mdate - tm(2022m1)) / 12
    generate moy = month(dofm(mdate))
    generate double x = target * t
    * main: relative to the platform's other complaints
    quietly ppmlhdfe count x, absorb(target mdate) vce(robust)
    local rt = _b[x]
    local rst = _se[x]
    local zr = (`rt' - rb) / sqrt(`rst'^2 + rsb^2)
    * secondary: raw growth of sexual-content complaints, HAC SE (6 lags)
    keep if target == 1
    tsset mdate
    quietly glm count t i.moy, family(poisson) vce(hac nwest 6)
    local t = _b[t]
    local st = _se[t]
    local z = (`t' - nb) / sqrt(`st'^2 + nsb^2)
    display "`plat'" _col(14) "share-adjusted " %6.3f exp(`rt') "  p vs police " %6.4f 2*normal(-abs(`zr')) ///
        "   |   raw " %7.3f exp(`t') "  p vs police " %6.4f 2*normal(-abs(`z'))
end

display _n "--- Platforms: growth per year (share-adjusted = main; raw = secondary)"
foreach p in Facebook Instagram X Snapchat Google {
    platgrowth `p'
}

* ---- Pooled five-platform summary (raw growth; five clusters only)
use "stata/platform_month_panel.dta", clear
drop if suspect_duplicate == 1
keep if inlist(platform, "Facebook", "Instagram", "X", "Snapchat", "Google")
keep if month >= "2022-01" & month <= "2024-12" & inlist(category_group, "sexual", "synthetic")
collapse (sum) count, by(platform month)
generate mdate = monthly(month, "YM")
generate double t = (mdate - tm(2022m1)) / 12
generate moy = month(dofm(mdate))
generate double lc = ln(count + 1)
encode platform, generate(pid)
display _n "--- Pooled platforms (rough summary, not a comparison between platforms)"
regress lc t i.pid i.moy, vce(cluster pid)
display "Pooled raw growth per year: " %6.3f exp(_b[t]) "  p vs police " ///
    %6.4f 2*normal(-abs((_b[t] - nb) / sqrt(_se[t]^2 + nsb^2)))

log close
