* =============================================================================
* part1_long.do  --  Part 1 over a longer period, 2013-2024
*   Outcome: sexual-content cyber crime by State (IT Act Sec 67 + 67A + 66E; child abuse
*   material excluded). NCRB's cyber crimes against women start only in 2017; this is the
*   closest series published before that. It counts offences, not female victims, and
*   2013-2015 is Sec 67 only (67A and 66E were not reported separately until 2016).
*   Units: 34 (Andhra Pradesh + Telangana merged for every year; NCRB reports them as one in 2013).
*   Built by scripts/part1_long.py (stata/state_category_year_long.dta, stata/national_long.dta).
*
*     Step 2 long  Model 1, 2013-2024, with checks
*     Step 1 pre   across States, 2013-2016 (and 2017-2024 on the same outcome)
*     Trend        India by year, 2013-2024
* Run from the repository root:   do stata/part1_long.do
* Output: stata/part1_long_results.txt; tables in stata/tables/ (part1_long_*)
* =============================================================================

run "/Users/Academic/Downloads/curly-octo-rotary-phone-claude-stata/stata/setup.do"
capture log close
log using "stata/part1_long_results.txt", text replace

* =============================================================================
* STEP 2 LONG  MODEL 1, 2013-2024
*   cases = exp(b x Cyber x Access x (year - 2013) + State x crime + State x year + crime x year)
*   Cyber = sexual-content cyber crime; comparison = five offline crimes against women.
*   Expected: NSS 2017 0.968 (p = 0.11, 21 States); CAMS 15+ 0.968 (0.16); NFHS-5 0.983 (0.51)
* =============================================================================
display _n "==================== STEP 2 LONG: MODEL 1, 2013-2024 ===================="
use "stata/state_category_year_long.dta", clear
fe_ids
tempfile long
save `long'

foreach x in access_nss2017_5plus access_cams2023_15plus access_nfhs5_15to49_avg {
    use `long', clear
    keep if inlist(grp, "cyber", "offline") & !missing(`x')
    generate cyber = grp == "cyber"
    zas `x' z
    generate double treat = cyber * z * (year - 2013)
    display _n "--- Model 1 long, access: `x'"
    eststo, title("`x'"): ppmlhdfe cases treat, absorb(sc st ct) vce(cluster sid)
    display "Rate ratio per SD per year: " %6.3f exp(_b[treat])
}
savetab part1_long_table1_model1 "Part 1, Model 1, 2013-2024: sexual-content cyber crime, extra yearly growth per SD of access"

* Checks (NSS 2017 unless named). Expected:
*   2017-2024 only 0.978 (0.29); 2013-2016 only 0.921 (0.012); 2014-2016 only 1.103 (0.43);
*   drop 2013 0.977 (0.26); CAMS 2013-2016 0.908 (0.024); CAMS 2014-2016 1.150 (0.36);
*   placebo, all other cyber crime 1.008 (0.85)
foreach r in y1724 y1316 y1416 drop2013 cams1316 cams1416 placebo {
    use `long', clear
    local x access_nss2017_5plus
    if inlist("`r'", "cams1316", "cams1416") local x access_cams2023_15plus
    local tg cyber
    if "`r'" == "placebo" local tg placebo
    keep if inlist(grp, "`tg'", "offline") & !missing(`x')
    local base 2013
    if "`r'" == "y1724" {
        keep if year >= 2017
        local base 2017
    }
    if inlist("`r'", "y1316", "cams1316") keep if year <= 2016
    if inlist("`r'", "y1416", "cams1416") {
        keep if inrange(year, 2014, 2016)
        local base 2014
    }
    if "`r'" == "drop2013" {
        keep if year >= 2014
        local base 2014
    }
    generate cyber = grp == "`tg'"
    zas `x' z
    generate double treat = cyber * z * (year - `base')
    display _n "--- Model 1 long check: `r' (access `x')"
    eststo, title("`r'"): ppmlhdfe cases treat, absorb(sc st ct) vce(cluster sid)
}
savetab part1_long_table2_checks "Part 1, Model 1 long: checks (NSS 2017 unless CAMS named)"

* =============================================================================
* STEP 1 PRE  ACROSS STATES, 2013-2016 (21 major States with NSS 2017 access)
*   cases = Access [+ log income] | year;  exposure = female population (2017 figure before 2017)
*   Expected: 2013-2016 access 1.28 (0.24); + income: access 1.50 (0.13), income 0.84 (0.60)
*             2017-2024 access 0.83 (0.52); + income: access 0.85 (0.65), income 0.99 (0.97)
* =============================================================================
display _n "==================== STEP 1 PRE: ACROSS STATES ===================="
foreach per in 1316 1724 {
    use `long', clear
    keep if grp == "cyber" & !missing(access_nss2017_5plus, nsdp_pc_avg)
    if "`per'" == "1316" keep if year <= 2016
    if "`per'" == "1724" keep if year >= 2017
    generate double ln_income = ln(nsdp_pc_avg)
    zas access_nss2017_5plus z_access
    zas ln_income z_income
    display _n "--- Step 1, sexual-content cyber crime, years `per'"
    eststo, title("`per'"): ppmlhdfe cases z_access, absorb(year) exposure(female_pop_lakh) vce(cluster sid)
    eststo, title("`per' + income"): ppmlhdfe cases z_access z_income, absorb(year) exposure(female_pop_lakh) vce(cluster sid)
}
savetab part1_long_table3_across "Part 1, Step 1: across States, sexual-content cyber crime (per SD)"

* =============================================================================
* TREND  INDIA BY YEAR, 2013-2024 (descriptive)
*   Expected: elasticity 1.33, R-squared 0.89; correlation of yearly growth 0.31 (11 years)
* =============================================================================
display _n "==================== INDIA BY YEAR, 2013-2024 ===================="
use "stata/national_long.dta", clear
tsset year
generate double l_users = ln(internet_users_mn)
generate double l_sex = ln(sexual_content_cases)
list year internet_users_mn sexual_content_cases, noobs sep(0)
export delimited year internet_users_mn sexual_content_cases using "stata/tables/part1_long_table4_national.csv", replace
regress l_sex l_users
generate double g_users = D.l_users
generate double g_sex = D.l_sex
correlate g_users g_sex
twoway (connected sexual_content_cases year, yaxis(1)) (connected internet_users_mn year, yaxis(2)), ///
    ytitle("Sexual-content cyber crime (NCRB)", axis(1)) ytitle("Internet users, million", axis(2)) ///
    xtitle("") xline(2016.75, lpattern(dash)) legend(order(1 "Sexual-content cyber crime" 2 "Internet users")) ///
    title("India: internet users and sexual-content cyber crime, 2013-2024") note("Dashed line: Jio launch, September 2016")
graph export "stata/tables/part1_long_figure1_national.png", replace width(1600)

log close
