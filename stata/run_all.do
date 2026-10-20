* =============================================================================
* run_all.do  --  runs all three parts
*   cd "path/to/curly-octo-rotary-phone"     (the folder that contains stata/)
*   do stata/run_all.do
* Results: stata/part1_results.txt, stata/part2_results.txt, stata/part3_results.txt, plus charts.
* =============================================================================

cd "/Users/Academic/Downloads/curly-octo-rotary-phone-claude-stata"
do "stata/part1.do"
do "stata/part1_long.do"
do "stata/part2.do"
do "stata/part3.do"
