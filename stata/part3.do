* =============================================================================
* part3.do  --  Part 3: police records versus complaints to platforms, 2022-2024
*   Follows the Methodology, Part 3:
*     A  Descriptive: police records and platform complaints by year; each platform's
*        sexual-content share of its complaints
*     B  MAIN model, share-adjusted (Steps 2-4): police = cyber vs offline crimes against women;
*        each platform = sexual-content vs its other complaints; z-test of each platform vs police
*     C  SECONDARY (Step 5): raw growth of the counts, and a pooled five-platform summary
* Platform categories: Facebook and Instagram "content showing me in nudity/partial nudity or in a
* sexual act"; X sensitive adult content + synthetic or manipulated media; Google (incl. YouTube)
* graphic sexual content; Snapchat sexual content. ShareChat and Moj stop in October 2022 (baseline).
* Run from the repository root:   do stata/part3.do
* Output: stata/part3_results.txt, stata/part3_yearly.png
* =============================================================================

run stata/setup.do
capture log close
log using "stata/part3_results.txt", text replace

* =============================================================================
* A  DESCRIPTIVE
* =============================================================================
display _n "==================== A: BY YEAR ===================="
use "stata/national_year.dta", clear
keep if inrange(year, 2021, 2025)
egen double platform_complaints = rowtotal(x_sexual x_synthetic meta_sexual google_sexual), missing
format cyber_vaw_cases platform_complaints snap_sexual sharechat_sexual meta_all x_all %12.0fc
display "Months covered (2021: June-December for most; X changed format from March 2025)"
list year x_months meta_months google_months snap_months sharechat_months, noobs sep(0)
list year cyber_vaw_cases platform_complaints snap_sexual sharechat_sexual, noobs sep(0)
display "Complaints to Meta and X for every reason (the complaint routes themselves)"
list year meta_all x_all, noobs sep(0)

preserve
    keep if inrange(year, 2022, 2024)
    twoway (connected platform_complaints year) (connected cyber_vaw_cases year), ///
        yscale(log) ylabel(1000 5000 20000 50000, format(%9.0fc)) xlabel(2022(1)2024) ///
        ytitle("Number (log scale)") xtitle("") ///
        legend(order(1 "Complaints to X, Facebook, Instagram, Google: sexual content" ///
        2 "NCRB cyber crimes against women") cols(1)) title("Complaints to platforms and police records, India")
    graph export "stata/part3_yearly.png", replace width(1800)
restore

* Each platform's sexual-content complaints as % of all its complaints (compare each platform
* with itself over time only). Months without a full breakdown dropped; X stops at Feb 2025.
* Expected (%), 2021-2025: Facebook 5.9 5.2 3.2 4.9 5.6; Instagram 7.9 1.7 9.3 4.9 2.8;
* Snapchat 41.0 26.8 19.3 20.3 22.5; X 9.2 6.8 7.4 14.4 44.1 (Jan-Feb); Google ~0;
* ShareChat 7.2 8.5; Moj 12.0 9.2
use "stata/platform_month_panel.dta", clear
drop if suspect_duplicate == 1
drop if platform == "X" & month >= "2025-03"
bysort platform month: egen has_other = max(category_group == "placebo")
keep if has_other
generate year = real(substr(month, 1, 4))
generate double target = count * inlist(category_group, "sexual", "synthetic")
collapse (sum) target count, by(platform year)
generate double share_pct = 100 * target / count
display _n "Sexual-content complaints, % of each platform's complaints"
tabdisp platform year if year <= 2025, cell(share_pct) format(%5.1f)

* =============================================================================
* B  MAIN MODEL: SHARE-ADJUSTED GROWTH, 2022-2024
*   Police:   cases = exp(b x Cyber x (year - 2022) + State x crime + State x year); SE by State
*   Platform: complaints = exp(t x Sexual x years since Jan 2022 + type + month); robust SE
*   z = (t - b) / sqrt(se_t^2 + se_b^2)
*   The month effects absorb anything that moves every complaint on a platform, such as the
*   2022 IT Rules amendment and the Grievance Appellate Committee (Meta: all complaints ~7x in 2023).
*   Expected: police 1.145 a year (1.04-1.27); Facebook 1.27 (p vs police 0.58); Instagram 1.09
*   (0.85); X 1.49 (0.47); Snapchat 0.84 (<0.001); Google 0.97 (0.32)
* =============================================================================
display _n "==================== B: MAIN MODEL (SHARE-ADJUSTED) ===================="
build_m
keep if inrange(year, 2022, 2024)
fe_ids
generate double x = cyber * (year - 2022)
display _n "--- Police: cyber vs offline crimes against women"
ppmlhdfe cases x, absorb(sc st) vce(cluster sid)
scalar rb = _b[x]
scalar rsb = _se[x]
display "Police share-adjusted growth per year: " %6.3f exp(rb)

* ---- Police, raw (used in C)
use "stata/state_year_panel.dta", clear
keep if inrange(year, 2022, 2024) & !missing(cyber_vaw_cases)
generate t = year - 2022
egen sid = group(state)
quietly ppmlhdfe cyber_vaw_cases t, absorb(sid) vce(cluster sid)
scalar nb = _b[t]
scalar nsb = _se[t]

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
    * main: sexual-content complaints relative to the platform's other complaints
    quietly ppmlhdfe count x, absorb(target mdate) vce(robust)
    local rt = _b[x]
    local rst = _se[x]
    local pr = 2 * normal(-abs((`rt' - rb) / sqrt(`rst'^2 + rsb^2)))
    * secondary: raw growth of sexual-content complaints, Newey-West SE (6 lags)
    keep if target == 1
    tsset mdate
    quietly glm count t i.moy, family(poisson) vce(hac nwest 6)
    local g = _b[t]
    local sg = _se[t]
    local praw = 2 * normal(-abs((`g' - nb) / sqrt(`sg'^2 + nsb^2)))
    display "`plat'" _col(13) "share-adjusted " %6.3f exp(`rt') " [" %5.2f exp(`rt' - 1.96 * `rst') "-" ///
        %5.2f exp(`rt' + 1.96 * `rst') "]  p vs police " %6.4f `pr' ///
        "  |  raw " %7.3f exp(`g') "  p vs police " %6.4f `praw'
end

display _n "--- Platforms, growth per year (share-adjusted = MAIN; raw = SECONDARY, see C)"
foreach p in Facebook Instagram X Snapchat Google {
    platgrowth `p'
}

* =============================================================================
* C  SECONDARY: RAW GROWTH AND POOLED SUMMARY
*   Raw growth mixes in growth of the complaint routes themselves, so it is reported second.
*   Expected raw: police 1.13; Facebook 3.74 (p < 0.001); Instagram 1.62 (0.34); X 11.62 (p < 0.001);
*   Snapchat 1.18 (0.49); Google 0.80 (0.013). Pooled 2.96 (p = 0.040).
*   The pooled estimate is a rough summary of the whole platform side against police growth, not a
*   ranking or comparison between individual platforms (five clusters only).
* =============================================================================
display _n "==================== C: SECONDARY ===================="
display "Police raw growth per year: " %6.3f exp(nb)
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
display _n "--- Pooled five platforms (rough summary)"
regress lc t i.pid i.moy, vce(cluster pid)
display "Pooled raw growth per year: " %6.3f exp(_b[t]) "  p vs police " ///
    %6.4f 2 * normal(-abs((_b[t] - nb) / sqrt(_se[t]^2 + nsb^2)))

log close
