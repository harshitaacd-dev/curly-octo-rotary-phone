* =============================================================================
* jio.do  --  The Jio shock and recorded sexual-content cyber crime, 2013-2022
*   Design from "Mobile Internet and Collective Action: Evidence from India's Jio Shock"
*   (SSRN 6959526): Jio launched on 5 September 2016 and cut data prices by over 90% everywhere at
*   once; States differed in how much of their population Jio's network reached at launch.
*   Coverage = share of the 2016 population (WorldPop) within 5 km of a Jio cell first seen by
*   31 December 2016 (OpenCellID, March 2017 dump). Built by scripts/jio_coverage.py and
*   scripts/jio_models.py (stata/state_category_year_long_jio.dta). Coverage enters per 10 points.
*
*     Main     cases = exp(b x Cyber x Post x Jio + State x crime + State x year + crime x year)
*              Cyber = sexual-content cyber crime; comparison = five offline crimes against women;
*              Post = 2017 onwards
*     Checks   window to 2024; Post from 2016; cells seen by Sep 2016 / Mar 2017; 7 km; drop 2013;
*              year x urban share and income; placebo date 2015 on 2013-2016; other cyber crime
*     Paper    one outcome at a time, State + year FE, female population exposure
*     Event    year-by-year, base 2016, joint pre-trend test
* Run from the repository root:   do stata/jio.do
* Output: stata/jio_results.txt; tables and figure in stata/tables/ (jio_*)
* =============================================================================

run "/Users/Academic/Downloads/curly-octo-rotary-phone-claude-stata/stata/setup.do"
capture log close
log using "stata/jio_results.txt", text replace

use "stata/state_category_year_long_jio.dta", clear
fe_ids
* Working copy at a fixed path (a tempfile name is not visible inside the program below)
save "stata/jio_work.dta", replace

* jtreat cov first last post [treated]: keeps the sample and builds treat = Cyber x Post x (10 x cov)
capture program drop jtreat
program define jtreat
    args cov first last post tg
    if "`tg'" == "" local tg cyber
    use "stata/jio_work.dta", clear
    keep if inlist(grp, "`tg'", "offline") & inrange(year, `first', `last') & !missing(`cov')
    generate cyb = grp == "`tg'"
    generate double treat = cyb * (year >= `post') * 10 * `cov'
end

* =============================================================================
* MAIN AND CHECKS
*   Expected: main 0.850 (p = 0.051; randomisation p = 0.048 in Python)
*   window 2013-2024 0.846 (0.037); Post from 2016 0.846 (0.059); Sep 2016 cells 0.932 (0.39);
*   Mar 2017 cells 0.848 (0.033); 7 km 0.842 (0.021); drop 2013 0.877 (0.12);
*   year x urban, income 0.793 (<0.001); placebo date 2015 0.933 (0.12); other cyber 0.983 (0.85)
* =============================================================================
display _n "==================== JIO: MAIN AND CHECKS ===================="
jtreat jio_cov5km_dec2016 2013 2022 2017
eststo, title("Main"): ppmlhdfe cases treat, absorb(sc st ct) vce(cluster sid)
display "Rate ratio per 10 points of coverage: " %6.3f exp(_b[treat])

jtreat jio_cov5km_dec2016 2013 2024 2017
eststo, title("To 2024"): ppmlhdfe cases treat, absorb(sc st ct) vce(cluster sid)
jtreat jio_cov5km_dec2016 2013 2022 2016
eststo, title("Post 2016"): ppmlhdfe cases treat, absorb(sc st ct) vce(cluster sid)
jtreat jio_cov5km_sep2016 2013 2022 2017
eststo, title("Sep 2016 cells"): ppmlhdfe cases treat, absorb(sc st ct) vce(cluster sid)
jtreat jio_cov5km_mar2017 2013 2022 2017
eststo, title("Mar 2017 cells"): ppmlhdfe cases treat, absorb(sc st ct) vce(cluster sid)
jtreat jio_cov7km_dec2016 2013 2022 2017
eststo, title("7 km"): ppmlhdfe cases treat, absorb(sc st ct) vce(cluster sid)
jtreat jio_cov5km_dec2016 2014 2022 2017
eststo, title("Drop 2013"): ppmlhdfe cases treat, absorb(sc st ct) vce(cluster sid)
savetab jio_table1_main "Jio coverage at launch: Cyber x Post x Coverage, per 10 points of coverage"

jtreat jio_cov5km_dec2016 2013 2022 2017
keep if !missing(urban_share_cams, ln_income)
foreach v in urban_share_cams ln_income {
    quietly summarize `v'
    generate double cy_`v' = cyb * (year - 2013) * (`v' - r(mean))
}
eststo, title("+ year x urban, income"): ppmlhdfe cases treat cy_urban_share_cams cy_ln_income, absorb(sc st ct) vce(cluster sid)
jtreat jio_cov5km_dec2016 2013 2016 2015
eststo, title("Placebo date 2015"): ppmlhdfe cases treat, absorb(sc st ct) vce(cluster sid)
jtreat jio_cov5km_dec2016 2013 2022 2017 placebo
eststo, title("Other cyber crime"): ppmlhdfe cases treat, absorb(sc st ct) vce(cluster sid)
savetab jio_table2_checks "Jio coverage at launch: further checks"

* =============================================================================
* THE PAPER'S DESIGN: one outcome, State + year fixed effects, female population exposure
*   Expected: sexual-content 0.814 (p = 0.011); other cyber 0.970 (0.75); offline (placebo) 0.968 (0.016)
* =============================================================================
display _n "==================== JIO: DOUBLE DIFFERENCE ===================="
foreach g in cyber placebo offline {
    use "stata/jio_work.dta", clear
    keep if grp == "`g'" & inrange(year, 2013, 2022) & !missing(jio_cov5km_dec2016)
    collapse (sum) cases (first) female_pop_lakh jio_cov5km_dec2016 sid, by(state year)
    generate double treat = (year >= 2017) * 10 * jio_cov5km_dec2016
    eststo, title("`g'"): ppmlhdfe cases treat, absorb(sid year) exposure(female_pop_lakh) vce(cluster sid)
}
savetab jio_table3_double "Jio coverage at launch: Post x Coverage, one outcome at a time"

* =============================================================================
* EVENT STUDY, base 2016
*   Expected (log points per 10 points): 2013 0.088 (0.057), 2014 -0.006, 2015 0.024;
*   2017 -0.035, 2018 -0.126 (0.010), 2019 -0.160 (0.006), 2020 -0.123 (0.020), 2021 -0.138, 2022 -0.146
*   Joint pre-trend test (2013-2015 = 0): chi2(3) = 4.42, p = 0.22
* =============================================================================
display _n "==================== JIO: EVENT STUDY ===================="
jtreat jio_cov5km_dec2016 2013 2022 2017
generate double j = 10 * jio_cov5km_dec2016
forvalues y = 2013/2022 {
    if `y' != 2016 generate double e`y' = cyb * (year == `y') * j
}
ppmlhdfe cases e2013 e2014 e2015 e2017-e2022, absorb(sc st ct) vce(cluster sid)
test e2013 e2014 e2015
display "Joint pre-trend test: chi2(" r(df) ") = " %5.2f r(chi2) ", p = " %5.3f r(p)
tempname es
postfile `es' year b lo hi using "stata/tables/jio_event.dta", replace
forvalues y = 2013/2022 {
    if `y' == 2016 post `es' (`y') (0) (0) (0)
    else post `es' (`y') (_b[e`y']) (_b[e`y'] - 1.96 * _se[e`y']) (_b[e`y'] + 1.96 * _se[e`y'])
}
postclose `es'
use "stata/tables/jio_event.dta", clear
export delimited using "stata/tables/jio_table4_event.csv", replace
list, noobs sep(0)
twoway (rcap lo hi year) (connected b year), yline(0) xline(2016.7, lpattern(dash)) ///
    xtitle("") ytitle("Log points per 10 points of coverage") legend(off) ///
    title("Sexual-content cyber crime vs offline crimes, by Jio coverage at launch") ///
    note("Base year 2016. Dashed line: Jio launch, September 2016. 95% intervals, SE clustered by State.")
graph export "stata/tables/jio_figure1_event.png", replace width(1600)

erase "stata/jio_work.dta"
log close
