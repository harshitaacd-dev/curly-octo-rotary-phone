# Technology Shocks and Tech-Facilitated Gender-Based Violence in India: Design Notes

**Question:** Can we say that technology shocks such as cheap Jio data (2016) or the AI boom (and with it nudify apps) are correlated with the rise in technology-facilitated gender-based violence (TFGBV)? Causal inference is not required; correlation is acceptable.

Background and full literature: `cheap-mobile-data-cybercrime-women-literature-review.md`.

## Short answer
Yes, as long as the claim matches the data. A descriptive paper is legitimate for a 4-week Master's project. Two things decide whether the correlation means anything.

## 1. Avoid a correlation that would show up anyway
Cheap data, AI tools and recorded cybercrime against women all rose after 2016. Any two upward-trending series are strongly correlated even if unrelated. To make the correlation informative:

- **Compare states, not national totals.** Do states where internet use grew faster after 2016 show faster growth in cybercrime against women?
- **Look for breaks at the shock dates.** Plot around September 2016 (Jio) and late 2022–2023 (generative AI). A visible bend in the trend is far more persuasive than a steady rise.
- **Use a comparison series.** Compare cybercrime against women with cyber fraud or cybercrime overall. Faster growth for crimes against women suggests a gendered pattern; equal growth suggests crime simply moving online.
- **Correlate changes, not levels.** Relate year-on-year changes to remove most of the shared upward trend.

## 2. Say clearly what is correlated
The outcome is **reported** TFGBV, not actual violence. Reporting got easier over the period: the National Cyber Crime Reporting Portal opened in 2019 with anonymous reporting for women. Suggested wording: "Rising internet access coincided with a rise in *recorded* cybercrime against women, which may reflect more abuse, more reporting, or both." Mark 2019 and COVID on all figures.

## The AI / nudify-app part
- **Global descriptive evidence:** Deeptrace's 2019 *State of Deepfakes* found 96% of deepfake videos online were non-consensual pornography, almost all targeting women. Graphika reported a 2,408% year-on-year rise in 2023 in social media links advertising "undressing" services, and 24 million visits to such sites in one month (this counts links, not users).
- **Indian data is weak:** the NCRB has no deepfake category. Its cybercrime-against-women tables include categories such as morphing and cyber pornography, where deepfakes would fall, but AI-generated abuse can't be isolated. Google Trends for India ("deepfake", "nudify") can serve as a rough interest measure alongside the NCRB morphing and pornography series. Keep this clearly descriptive.

## Suggested framing: two technology shocks
- **Jio (2016):** cheap data made far more people reachable online.
- **Generative AI (2022 onwards):** tools for making abusive images became widely available.

Document how recorded cybercrime against women changed around each, using the four checks above. A defensible claim: "Recorded technology-facilitated violence against women in India rose after both shocks, faster than other cybercrime and faster in states with greater exposure." Do not claim the shocks *caused* the rise.

## Feasible design (if moving beyond pure correlation)
- **Data:** state-by-year NCRB "Crime in India" counts of cybercrimes against women (~2014–2022; check which years have the women-specific breakdown); exposure before 2016 from TRAI subscriber data or NFHS-4.
- **Method:** difference-in-differences comparing more- vs less-exposed states before and after September 2016, controlling for the 2019 portal and COVID.
- **Checks:** placebo on crimes not aimed at women; compare with NFHS-4 vs NFHS-5 domestic violence modules.
- **Caveats:** secondary sources quote conflicting NCRB counts because categories changed; use original tables and document definitions. Cybercrime tables appear to be state- and city-level only, not district-level (verify).

## Sources
- [Deeptrace, State of Deepfakes 2019 (summary)](https://siliconrepublic.com/?p=843759), [report PDF](https://axbom.com/content/files/2023/06/deepfake_report.pdf)
- [Graphika findings on nudify services (Fortune)](https://fortune.com/2023/12/08/ai-pps-undress-women-photos-soaring-in-use), [Deccan Herald](https://www.deccanherald.com/technology/apps-that-use-ai-to-undress-women-in-photos-soaring-in-use-2803981)
- [New America on synthetic intimate imagery](https://www.newamerica.org/future-security/reports/a-weapon-against-women-in-politics/defining-nonconsensual-synthetic-intimate-imagery/)
- [NCRB state-wise cyber crimes against women (data.gov.in)](https://www.data.gov.in/resource/stateut-wise-number-cyber-crimes-against-women-during-2022), [The News Minute on NCRB categories](https://www.thenewsminute.com/news/most-cybercrimes-2021-reported-from-telangana-ncrb-data-shows-167337)
- [National Cyber Crime Reporting Portal launch](https://www.thenewsminute.com/news/citizens-now-can-report-cyber-crimes-online-115900)
