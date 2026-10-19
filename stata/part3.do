* =============================================================================
* part3.do  --  Part 3: crimes against women in NCRB versus online reports
*
*   3a  Reporting funnel: each stage in 2024 as a multiple of 2023
*   3b  Year by year, 2021-2025: platform complaints, NCRB cases, news incidents
*   3c  Monthly model: did platform complaints jump when Grok's image tools launched?
*
* Run from the repository root:   do stata/part3.do
* Needs (once): ssc install ftools ; ssc install reghdfe ; ssc install ppmlhdfe
* Output: stata/part3_results.txt (log), stata/part3_funnel.png, stata/part3_yearly.png,
*         stata/part3_meta_share.png
* =============================================================================

version 16
clear all
set more off
capture log close
log using "stata/part3_results.txt", text replace

foreach p in ftools reghdfe ppmlhdfe {
    capture which `p'
    if _rc ssc install `p', replace
}

* =============================================================================
* 3a  REPORTING FUNNEL, 2023 to 2024 (national totals)
*   Online stages rise (X 18-21x) while NCRB counts fall (0.95x). The national cyber crime
*   portal publishes no category breakdown ("missing" stage).
* =============================================================================
display _n "==================== 3a FUNNEL ===================="
use "stata/funnel_2023_2024.dta", clear
generate order = _n
list stage source y2023 y2024 ratio_2024_to_2023, noobs sep(0) abbreviate(20)
generate double log2_ratio = ln(ratio_2024_to_2023) / ln(2)
graph hbar log2_ratio if kind != "missing", over(stage, sort(order) label(labsize(vsmall))) ///
    ytitle("Change 2023 to 2024, doublings (0 = no change, 1 = 2x, -1 = half)") ///
    title("Online stages rise, police records do not") bar(1, color(navy))
graph export "stata/part3_funnel.png", replace width(1800)

* =============================================================================
* 3b  YEAR BY YEAR, 2021-2025
*   platform_complaints = complaints about sexual or synthetic content to X, Meta and Google
*   (as in the funnel); Snapchat user reports are shown separately (different scale and
*   definition). Meta is also shown as a share of all complaints to Meta, because the
*   complaint route itself grew about 7x in 2023.
*   Expected: platform complaints 1,981 (2022), 24,997 (2023), 51,763 (2024);
*   per NCRB case 0.14, 1.28, 2.78.
* =============================================================================
display _n "==================== 3b YEAR BY YEAR ===================="
use "stata/national_year.dta", clear
keep if inrange(year, 2021, 2025)
egen double platform_complaints = rowtotal(x_sexual x_synthetic meta_sexual google_sexual), missing
generate double complaints_per_ncrb_case = platform_complaints / cyber_vaw_cases
format platform_complaints cyber_vaw_cases snap_sexual %12.0fc
format complaints_per_ncrb_case meta_sexual_share_pct %6.2f

display _n "Months covered: 2021 is June-December only; X changed format from March 2025."
list year x_months meta_months snap_months, noobs sep(0)
list year platform_complaints cyber_vaw_cases complaints_per_ncrb_case, noobs sep(0)
list year x_sexual x_synthetic meta_sexual meta_all meta_sexual_share_pct snap_sexual, noobs sep(0)
list year news_ai_deepfake news_morphed news_real_or_unspecified news_all_incidents, noobs sep(0)

* Chart: full years only (2022-2024 for NCRB; 2025 platform data shown where available)
preserve
    keep if year >= 2022
    twoway (connected platform_complaints year) (connected cyber_vaw_cases year) ///
        (connected news_all_incidents year, yaxis(2)), ///
        yscale(log) ylabel(1000 10000 50000, format(%9.0fc)) ///
        ytitle("Complaints / cases (log scale)") ytitle("News-reported incidents", axis(2)) xtitle("") ///
        legend(order(1 "Platform complaints: sexual or synthetic content" 2 "NCRB cyber crimes against women" ///
        3 "News-reported incidents (right axis)") cols(1)) ///
        title("Online complaints and police records, India")
    graph export "stata/part3_yearly.png", replace width(1800)
restore

twoway connected meta_sexual_share_pct year, ytitle("% of all complaints to Facebook and Instagram") xtitle("") ///
    title("Meta: complaints about one's own intimate images, share of all complaints")
graph export "stata/part3_meta_share.png", replace width(1600)

* =============================================================================
* 3c  MONTHLY MODEL: Grok launch dates
*   For one platform, monthly complaints in a target group versus all other complaints to the
*   same platform:
*     count = Target x Grok-2 images (Aug-Nov 2024) + Target x Grok free for all (Dec 2024 on)
*             | month + group   [+ group-specific linear trend]
*   Month fixed effects absorb anything that moves all complaints together (e.g. the complaint
*   route growing). Robust SE (one platform, two groups: no clusters).
*   X runs to Feb 2025 (format change in Mar 2025). Snapchat Nov 2025 dropped (duplicate).
*   Expected (Python, no trend): X synthetic media, Grok free 17.8x (p < 0.001);
*   X sexual 0.33x (p = 0.09); Facebook sexual 1.43x (0.12); Instagram 0.22x (0.004);
*   Snapchat 1.45x (p < 0.001). With trend: X synthetic 22.8x (p = 0.001).
*   Descriptive: many things changed on X in late 2024; read as timing evidence, not as causal.
* =============================================================================
display _n "==================== 3c MONTHLY GROK MODEL ===================="
capture program drop grokmodel
program define grokmodel
    args plat groups endm
    use "stata/platform_month_panel.dta", clear
    drop if suspect_duplicate == 1
    keep if platform == "`plat'" & month <= "`endm'"
    generate target = 0
    foreach g of local groups {
        replace target = 1 if category_group == "`g'"
    }
    collapse (sum) count (max) grok2_images post_grok_free, by(month target)
    generate mdate = monthly(month, "YM")
    format mdate %tm
    generate double tg2 = target * grok2_images
    generate double tpf = target * post_grok_free
    generate double ttrend = target * (mdate - 700)
    display _n "--- `plat', target: `groups' (to `endm')"
    ppmlhdfe count tg2 tpf, absorb(mdate target) vce(robust)
    display "Grok-2 images: " %6.2f exp(_b[tg2]) "   Grok free for all: " %6.2f exp(_b[tpf])
    display "--- with group-specific trend"
    ppmlhdfe count tg2 tpf ttrend, absorb(mdate target) vce(robust)
    display "Grok-2 images: " %6.2f exp(_b[tg2]) "   Grok free for all: " %6.2f exp(_b[tpf])
end

grokmodel X "synthetic" "2025-02"
grokmodel X "sexual" "2025-02"
grokmodel X "synthetic sexual" "2025-02"
grokmodel Facebook "sexual" "2026-12"
grokmodel Instagram "sexual" "2026-12"
grokmodel Snapchat "sexual" "2026-12"

* Monthly chart: X complaints by group
use "stata/platform_month_panel.dta", clear
keep if platform == "X" & month <= "2025-02" & inlist(category_group, "synthetic", "sexual")
collapse (sum) count, by(month category_group)
generate mdate = monthly(month, "YM")
format mdate %tm
twoway (line count mdate if category_group == "synthetic") (line count mdate if category_group == "sexual"), ///
    xline(`=tm(2024m8)' `=tm(2024m12)', lpattern(dash)) xtitle("") ytitle("Complaints to X, India") ///
    legend(order(1 "Synthetic or manipulated media" 2 "Sensitive adult content")) ///
    title("Complaints to X; dashed lines: Grok-2 images (Aug 2024), Grok free (Dec 2024)")
graph export "stata/part3_x_monthly.png", replace width(1800)

log close
