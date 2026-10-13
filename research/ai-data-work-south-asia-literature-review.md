# AI Data Work in South Asia: Extraction or Opportunity? A Literature Review of Who Does It, What It Pays, and Why

## Abstract

Online microwork and outsourced data annotation are often described as the hidden labour behind the AI boom, and South Asia, India above all, is one of the largest sources of it. This review asks three questions: who does the work (in particular, whether it is mainly done by South Asian women); what it pays and why; and what research designs and data an econometric study could build on. We searched along five angles (critical data-work studies, the labour economics of online platforms, gender and development economics, measurement and data infrastructure, and policy and standards) and verified 34 works. Three findings stand out. First, the large quantitative sources describe the open-platform segment of this workforce as mostly male, including in India. Women appear more often in managed outsourcing centres and home-based arrangements, which are hard to see in the data. Second, pay is low and gender gaps are consistently documented, but they work mostly through constrained choices: which tasks women pick, how they bid, and how often their work is interrupted. They do not come mainly from lower pay for the same task. Third, two literatures describe the same low wages in incompatible terms. Ethnographic studies call them extraction rooted in power; economists explain them either as employer wage-setting power (monopsony, which is extraction in a measurable sense) or as the result of poor alternatives (which is not). No retrieved study separates these explanations for South Asian women doing AI data work. That empty cell is where an econometric paper can contribute.

## 1. Introduction

Before 2010, studies of Amazon Mechanical Turk's workforce described mostly American workers. By 2010 the workforce had become increasingly international, with a large share of young, well-educated Indian workers [1]. Since then, data work has moved from open marketplaces into a layered supply chain of AI companies, annotation vendors, "impact-sourcing" firms and rural delivery centres, much of it in India. Two literatures have grown around this shift and rarely cite each other. Ethnographers, sociologists and computer scientists who study how people work with technology (the HCI field) document power, control and precarity in data work. Labour economists study online platforms as markets, measuring pay, hiring frictions and employer power. A researcher who wants to make the claim "data work done by South Asian women is extractive and underpaid" needs both: the first supplies the hypothesis, the second supplies the tools to test it.

This review answers three research questions:

- **RQ1.** Who does AI and online data work in South Asia by gender and country, and how strong is the evidence for a mostly-female workforce?
- **RQ2.** What does published research find about pay levels, gender pay gaps, and the mechanisms behind low pay (employer power, information frictions, alternatives open to workers)?
- **RQ3.** Which research designs and datasets have been used, and which combination of question, design and data has not yet been studied?

Section 2 describes the search. Section 3 lays out how the literature is organised. Sections 4 to 6 develop the evidence for each question. Section 7 compares across the branches, Section 8 lists open problems, and Section 9 answers the research questions.

## 2. Methodology

**Search angles.** (a) Critical and ethnographic studies of data work; (b) the labour economics of online platforms (pay, employer power, hiring); (c) gender and development economics on women's work in South Asia, including outsourcing and home-based work; (d) measurement and data infrastructure (indices, labour force surveys); (e) policy and labour standards. The angles were run one after another by a single researcher; the method calls for parallel runs, but it is unchanged otherwise.

**Main keyword groups.** data annotation + India + workers; Mechanical Turk + demographics / earnings; online labour + gender pay gap; monopsony + online labour market / gender; BPO / home-based work + women + India + experiment; online labour index; digital work + Pakistan / Bangladesh + gender; impact sourcing + AI supply chain.

**Time range.** 2010 to 2026, with more weight on work after 2018.

**Inclusion.** Peer-reviewed articles, major working-paper series (NBER, CESifo, MPRA, STEG) and institutional reports (ILO, World Bank, Fairwork) whose existence, authors and main claim we confirmed. **Exclusion.** Journalism is used only for context and never as evidence. Works whose authorship could not be confirmed were dropped (for example, an arXiv experiment on annotator pay and instructions, arXiv:2312.14565). Numbers are quoted only where they appear in an abstract or a primary summary we retrieved.

**Final corpus.** 34 works.

**Evidence types used in this review:**

| Evidence type | What it is | Credibility for causal claims |
|---|---|---|
| Ethnography / interviews | Fieldwork in outsourcing centres or on platforms; dozens of informants | Strong on how the work is organised; cannot measure size or cause |
| Platform log data (descriptive) | Records of tasks, pay and bids, scraped or shared by platforms | Strong on levels and gaps; weak on why they exist |
| Surveys of workers | ILO, World Bank and university surveys; national labour force surveys | Representative only if the sampling frame is; usually descriptive |
| Quasi-experiments | Using naturally occurring variation, e.g. pay changes or trade shocks, to estimate effects | Moderate to strong if the assumptions hold |
| Field experiments (RCTs) | Randomised job offers, recruiting or hiring | Strongest for causal claims; tied to one setting |

## 3. How the literature is organised

We sort the literature along two dimensions: **what question a study asks** (who works; what they earn; why pay is set where it is; how the work is organised) and **what kind of evidence it uses** (qualitative; descriptive quantitative; causal).

| | Qualitative | Descriptive quantitative | Causal |
|---|---|---|---|
| **Who works** | [8], [9], [10] | [1], [2], [3], [4], [5], [6], [7] | (none) |
| **What they earn** | [13] (in part) | [2], [7], [11], [14], [15], [16], [17] | [12] (experimental reservation wage) |
| **Why pay is set there** | [28], [30], [32], [33] | [22], [23] | [18], [19], [20], [21], [24], [25] |
| **How the work is organised** | [8], [9], [28], [29], [30], [31], [32], [33] | [34] | (none) |

Three cells matter most. First, **no causal study of who enters this work** was retrieved: nobody has estimated what draws women versus men into AI data work. Second, the **causal studies of pay** come from Mechanical Turk [18], Upwork's predecessor oDesk [20], [21] and Brazilian manufacturing [19], not from South Asian annotation. Third, the causal studies of **women's job take-up in India** [24], [25] study outsourcing (BPO) jobs and home-based data entry rather than AI annotation, though they come closest. One work straddles the categories usefully: Chopra et al. [26] is a technology-design study, but it doubles as early evidence on rural Indian workers' demand for paid digital tasks.

## 4. Who does the work: data shows a mostly male platform workforce, while evidence on women is mostly qualitative (RQ1)

The quantitative sources agree with one another, and they cut against a premise that the work is mostly done by women. Ross et al. [1] documented the early shift of Mechanical Turk toward young, educated Indian workers, and their account of the "typical" worker moved away from the stay-at-home American mother. Hara et al. [2] later linked work logs to a demographic survey and found a large pay gap by country between US and Indian workers on the same platform. At the level of the whole online freelance market, the Online Labour Index [3] tracks vacancies on major platforms in close to real time. Its 2020 extension [4] added gender estimates, guessed from first names, which put women in a minority of online labour supply overall and a smaller minority in India, the largest supplying country. The World Bank's 17-country survey [5] comes from the same measurement tradition and says outright that household labour surveys rarely capture these workers.

The South Asian surveys add detail without overturning the pattern. Sarker et al. [6] surveyed 242 men and 201 women doing gig work in Bangladesh. They found the market split by gender across platforms and task types, with women choosing digital work to manage several responsibilities while men cited income. This is the first sign that women's labour supply works differently from men's, which matters for Section 5. Shoib and Lohana [7] use Pakistan's Labour Force Survey 2024–25, which they describe as the first national dataset to identify online and digital workers separately. They find an earnings premium for digital work and an earnings penalty for women in both digital and physical work.

The evidence that women are concentrated in the work comes from a different part of the supply chain and from different methods. Wang, Prabhat and Sambasivan [8] interviewed 25 Indian annotators along with industry experts and AI practitioners. Chandhiramowuli et al. [9] did ethnography in two Indian annotation outsourcing centres. Gray and Suri [10] studied on-demand workers in the US and India and note that flexibility and anonymity help some female workers. None of these studies sets out to count workers by gender. Journalism and industry sources (not used as evidence here) describe rural centres that hire mainly women and vendors with roughly equal numbers of men and women.

**Which side is right depends on where you look in the supply chain.** Open-marketplace data [1]–[5] shows a male majority. Managed vendors and impact-sourcing centres, the segment ethnographers study [8], [9], may employ many more women, but no study has counted them. Neither side refutes the other, because they measure different parts of the chain. As a general claim about all AI data work, the premise is not supported. As a claim about the managed, home-based or rural-centre segment, it is plausible but unmeasured.

| Source | Segment covered | Gender measure | Finding on women |
|---|---|---|---|
| Ross et al. [1] | Mechanical Turk | Survey | Workforce moved toward young Indian workers |
| Stephany et al. [4] | Online freelance platforms | Guessed from first names | Minority, smaller in India |
| Sarker et al. [6] | Bangladesh gig work | Survey | Work split by gender; different reasons for working |
| Shoib & Lohana [7] | Pakistan, nationally representative | Labour force survey | Earnings penalty for women in digital work |
| Wang et al. [8]; Chandhiramowuli et al. [9] | Indian annotation vendors | Ethnography | Not counted |

*Table 1. Every source that measures gender finds women in a minority on open platforms. The segment where women are said to be concentrated has not been counted.*

## 5. Pay: low, unequal by gender, and the gaps run through constrained choices (RQ2, levels and gaps)

On pay levels, platform log studies agree. Hara et al. [11] recorded 2,676 workers doing 3.8 million Mechanical Turk tasks and found a median of about $2 an hour, with only 4% earning above the US federal minimum wage. Requesters' average pay was higher, but the lowest payers posted most of the work, and the estimates depend on how unpaid time, such as searching for tasks, is counted. The follow-up [2] put Indian workers' average at less than half the US average. Horton and Chilton [12] earlier estimated workers' reservation wages (the lowest pay at which they will work) from experiments, finding them roughly log-normal around a low median. Horton later warned that this figure rested on strong assumptions and had been over-used. The ILO's survey of about 3,500 workers in 75 countries across five microtask platforms [13] reached a similar conclusion from a different angle: workers doing valuable tasks for successful firms often earn low wages without employment protection.

Every quantitative study that looked found a gender gap. But in each one, the gap travels through choices women make under constraints rather than through lower pay for the identical task. Litman et al. [14] found women on Mechanical Turk earned about 10.5% less per hour, largely because they chose tasks with lower advertised pay. Adams and Berg [15] point to home responsibilities, as their title "When Home Affects Pay" signals. Foong et al. [16] found that the median woman on Upwork set an hourly rate 74% of the median man's, even after controlling for experience, education and job category, while total earnings were sometimes similar because women worked more hours. Gomez-Herrera and Müller-Langer [17] are the clearest case. On PeoplePerHour, a 4% project-level gap shrinks to about 0.3% and loses statistical significance once workers' bids are controlled for. Women bid lower and win more often. The only South Asian estimate, from Pakistan [7], is larger and comes from a national survey rather than platform logs, so it captures differences in who sorts into which jobs, not just pay per task.

| Study | Setting | Gap found | Main channel |
|---|---|---|---|
| Litman et al. [14] | Mechanical Turk, 22,271 workers | Women earn about 10.5% less per hour | Choice of lower-paid tasks |
| Foong et al. [16] | Upwork, 48,019 US workers | Median rate 74% of men's | Self-set rates; hours offset it |
| Gomez-Herrera & Müller-Langer [17] | PeoplePerHour, 2.5 million bids | 4% gap, about 0.3% after controlling for bids | Lower bids |
| Adams & Berg [15] | Crowdwork | Gap present | Home responsibilities (abstract-level only) |
| Shoib & Lohana [7] | Pakistan labour force survey | 22.5% penalty for women | Not separated |

*Table 2. On platforms, gender gaps mostly disappear once task choice and bids are controlled for, so the economic question is why women's choices are constrained.*

The common thread is important for an economics paper. If women accept lower-paid tasks and bid lower because they have fewer alternatives, the gap is not discrimination per task. It is a sign of **lower responsiveness of women's work to pay**, which is exactly what the employer-power models in Section 6 predict.

## 6. Why pay is low: three economic explanations, and the critical tradition that calls it extraction (RQ2, mechanisms)

The economics literature offers three explanations for low wages in this kind of work. They have different implications for whether "extractive" is the right word.

**Explanation 1: employer wage-setting power (monopsony).** Dube et al. [18] combined machine-learning estimates on scraped Mechanical Turk tasks with a reanalysis of five pay-randomising experiments. They found that workers barely respond to a requester's pay (an elasticity around 0.1), implying substantial employer power even in a market with low search costs. Sharma [19] supplies the missing gender link in a different setting. In Brazil she uses the end of the Multi-Fiber Arrangement, a textile trade quota, as a source of shocks to firms and finds that women are much less likely than men to leave after a wage cut. Her model attributes a large share of the gender wage gap to that difference, coming partly from women's preference for their particular employer and partly from having fewer good employers. Put together, [18] and [19] give a testable mechanism that no retrieved study has applied to South Asian data work: if constraints on mobility and home duties make women's work less responsive to pay, employers' power over them is larger, and so is the gap between their pay and the value of their work. In this explanation, "extraction" has a precise meaning: the share of the value a worker produces that is not paid to them.

**Explanation 2: information frictions.** Agrawal, Lacetera and Lyons [20] show that employers in developed countries are less likely to hire workers from less developed countries on an online contract-labour platform, and that verified work-history information benefits those workers disproportionately. Pallais [21] hired randomly chosen inexperienced data-entry applicants on oDesk and showed that employers under-invest in trying out new workers, leaving some of them inefficiently unemployed. These frictions lower pay for South Asian workers without implying that any one employer exploits them, and they can be fixed with better information.

**Explanation 3: poor alternatives.** Graham, Hjorth and Lehdonvirta [22] and Wood et al. [23] studied online workers in Sub-Saharan Africa and Southeast Asia and found real gains (income, flexibility, autonomy) alongside low pay, overwork and algorithmic control. Development economics shows how much access to such work can matter for South Asian women specifically. Jensen [24] randomly placed outsourcing-industry (BPO) recruiters in rural Indian villages and found that young women became more likely to work, more likely to study, and less likely to marry or have children early. Ho, Jalota and Karandikar [25] offered short-term data-entry jobs to women outside the labour force in West Bengal. Allowing the work to be done at home roughly tripled take-up, from 15% for an office job to 48%, at a cost in productivity, and acted as a gateway to later work outside the home. Chopra et al. [26] found rural Indian workers so keen on paid digitisation tasks that the authors recommended capping usage. Jayachandran [27] explains why: social norms suppress women's employment in many developing countries beyond what income levels predict. In this explanation, low pay reflects women's narrow set of alternatives, and the work can be underpaid by global standards yet still improve on what women could otherwise earn.

**The critical tradition** describes the same wages as extraction rooted in power and the organisation of work. Miceli and Posada [28] analysed 210 instruction documents and 55 interviews in Venezuela and Argentina and found that workers' economic dependence makes them obedient while instructions impose clients' worldviews. Muldoon et al. [30] studied Sama, a firm marketed as ethical, in Kenya and Uganda and reported low wages, tight discipline, and gender-based exploitation and harassment. They argue that competition pushes impact-sourcing firms to trade social impact for margins. Irani [32] and Posada [33] place the work within global hierarchies, and Posada does so explicitly in terms of coloniality. Sambasivan and Veeraraghavan [29] show the same dynamic among skilled workers: domain experts in low-resource settings get treated as mere data collectors. Wang et al. [8] and Chandhiramowuli et al. [9] bring this to India: annotation is organised from the top down and governed by counting. Tubaro et al. [31] classify the roles human workers play in AI (training, verifying, imitating), and Fairwork [34] ranks microwork platforms among the worst for fair working conditions.

**These literatures disagree, and the disagreement can be tested.** The critical tradition and explanation 1 agree that low pay comes from power. Explanation 3 says it comes from the absence of alternatives. Explanation 2 says it comes from missing information. They predict different things. Monopsony predicts that pay falls short of the value of output, and falls shorter for workers who respond less to pay. The alternatives explanation predicts pay close to what similar women earn elsewhere and large gains from access to the work. The information explanation predicts that verified records or credentials raise pay. Jensen [24] and Ho et al. [25] are compatible with both monopsony and alternatives, because a job can improve on a woman's alternatives and still pay her far less than the value she produces. That is exactly why the "extraction versus opportunity" framing is a false choice. Both can be true at once, and the share of each can be measured.

## 7. Comparing across the branches

Three patterns run across all the branches.

First, **the evidence is concentrated in the wrong segment.** Nearly all quantitative pay evidence ([2], [11], [14], [16], [17], [18]) comes from open Western marketplaces before the generative-AI boom. The segment where South Asian women are said to be concentrated (managed vendors, rural centres, home-based annotation) has only been studied with ethnography [8], [9], [30]. The demand shock from large language models (preference ranking, red-teaming, expert annotation) appears in none of the retrieved economic studies.

Second, **gender is measured badly where pay is measured well, and the reverse.** Platform logs give precise pay but guess gender from names [4] or from self-reports in US samples [16]. National surveys measure gender properly but, until recently, could not identify data workers at all [5]. Pakistan's 2024–25 survey [7] is the first South Asian exception retrieved. India's 2026 labour force survey reportedly adds questions on digital and platform work, but we found no published research using it yet.

Third, **the causal designs that exist answer neighbouring questions.** Pay elasticities [18], [19], hiring frictions [20], [21] and women's job take-up [24], [25] all have credible identification, but none sits at the intersection of South Asia, women and AI data work. The approaches transfer, but they have not been applied there yet.

## 8. Open problems and future directions

1. **Women's responsiveness to pay in South Asian data work.** The causal × why-pay × South Asian women cell is empty. Dube et al. [18] and Sharma [19] give the method: estimate how much women's work responds to pay variation on a platform or vendor, and convert it into the share of value they are not paid. A finding that women respond less than men doing identical tasks would turn "extractive" into a measured number.
2. **Counting women in the managed segment.** Section 4 shows the premise is untested where it is most plausible. A vendor partnership, or a survey sampled from annotation centres, would settle it. The ethnographic sites in [8], [9] show such centres can be reached.
3. **Pay compared with alternatives using national surveys.** Pakistan's survey [7] now identifies digital workers; India's 2026 survey reportedly will. Comparing data-work pay with what the same women would earn in other jobs, matched on district, education and home-based status, would test explanation 3 directly.
4. **The generative-AI demand shock.** None of the economic studies covers the period after 2022. Comparing districts with more or fewer annotation centres before and after the shock would test whether the boom raised women's employment, their pay, or neither.
5. **Supply-chain rent division.** Muldoon et al. [30] argue that competition squeezes impact-sourcing margins, but no retrieved work measures how value divides among client, vendor and worker. Company filings could give a first estimate.
6. **Home-based work as a choice under constraint.** Ho et al. [25] show that working from home both widens access and lowers productivity. Whether annotation vendors charge women for that flexibility through lower pay (a compensating wage differential) or through employer power is untested [unconfirmed: no work retrieved on pay for home-based annotation].

## 9. Conclusion

**RQ1.** The best quantitative evidence [1]–[5] describes the open-platform AI and online data workforce, including in India, as mostly male, with women a minority and sorted into different tasks [6]. Evidence that women are concentrated in the work exists only for managed and home-based segments, and only qualitatively [8]–[10]. The premise "mainly done by South Asian women" is therefore unsupported as a general claim and unmeasured for the segment where it is most plausible.

**RQ2.** Pay is low by any rich-country benchmark [11]–[13], with a large gap between countries [2]. Gender gaps are consistent [7], [14]–[17], but on platforms they work mostly through task choice, bids and interruptions. Three explanations account for low pay: employer power [18], [19], information frictions [20], [21] and poor alternatives [22]–[27]. They make different predictions, and they are not mutually exclusive. Women's limited responsiveness to pay, documented elsewhere [19] and implied by the evidence on constrained choices, makes the employer-power explanation the strongest candidate for a gendered, measurable definition of "extraction".

**RQ3.** Designs used so far include platform log analysis, randomised pay or hiring, trade-shock quasi-experiments, and village- or household-level RCTs. Usable data includes the Online Labour Index [3], [4], Mechanical Turk replication data [18], the World Bank survey [5], Pakistan's 2024–25 labour force survey [7] and, prospectively, India's 2026 survey. The unstudied combination is a causal estimate of women's responsiveness to pay and their resulting pay shortfall in South Asian AI data work.

**This review's contribution** is to show that "extraction versus opportunity" is a false choice. The two literatures describe the same wages, and economics can measure how much of the shortfall comes from employer power and how much from poor alternatives.

*Correction to an earlier answer in this conversation:* the result that working from home roughly tripled job take-up among women comes from Ho, Jalota and Karandikar's study of data-entry jobs in West Bengal [25], not from a J-PAL evaluation of Karya. We found no published randomised evaluation of Karya's earnings effects.

## References

[1] J. Ross, L. Irani, M. S. Silberman, et al., "Who Are the Crowdworkers? Shifting Demographics in Mechanical Turk," CHI Extended Abstracts, 2010.
[2] K. Hara, A. Adams, K. Milland, et al., "Worker Demographics and Earnings on Amazon Mechanical Turk: An Exploratory Analysis," CHI Extended Abstracts, 2019.
[3] O. Kässi, V. Lehdonvirta, "Online Labour Index: Measuring the Online Gig Economy for Policy and Research," Technological Forecasting and Social Change, 2018.
[4] F. Stephany, O. Kässi, U. Rani, et al., "Online Labour Index 2020: New Ways to Measure the World's Remote Freelancing Market," Big Data & Society, 2021.
[5] N. Datta, R. Chen, et al., "Working Without Borders: The Promise and Peril of Online Gig Work," World Bank, 2023.
[6] M. R. Sarker, T. A. Taj, M. A. R. Sarkar, et al., "Gender Differences in Job Satisfaction among Gig Workers in Bangladesh," Scientific Reports, 2024.
[7] Z. Shoib, S. Lohana, "Digital Work, Earnings Premiums, and the Gender Gap: Evidence from Pakistan's Labour Force Survey 2024–25," MPRA Working Paper 129903, 2026.
[8] D. Wang, S. Prabhat, N. Sambasivan, "Whose AI Dream? In Search of the Aspiration in Data Annotation," CHI, 2022.
[9] S. Chandhiramowuli, A. S. Taylor, S. Heitlinger, et al., "Making Data Work Count," Proceedings of the ACM on Human-Computer Interaction (CSCW), 2024.
[10] M. L. Gray, S. Suri, "Ghost Work: How to Stop Silicon Valley from Building a New Global Underclass," Houghton Mifflin Harcourt, 2019.
[11] K. Hara, A. Adams, K. Milland, et al., "A Data-Driven Analysis of Workers' Earnings on Amazon Mechanical Turk," CHI, 2018.
[12] J. J. Horton, L. B. Chilton, "The Labor Economics of Paid Crowdsourcing," ACM Conference on Electronic Commerce, 2010.
[13] J. Berg, M. Furrer, E. Harmon, et al., "Digital Labour Platforms and the Future of Work: Towards Decent Work in the Online World," International Labour Office, 2018.
[14] L. Litman, J. Robinson, Z. Rosen, et al., "The Persistence of Pay Inequality: The Gender Pay Gap in an Anonymous Online Labor Market," PLOS ONE, 2020.
[15] A. Adams, J. Berg, "When Home Affects Pay: An Analysis of the Gender Pay Gap among Crowdworkers," SSRN Working Paper, 2017.
[16] E. Foong, N. Vincent, B. Hecht, et al., "Women (Still) Ask For Less: Gender Differences in Hourly Rate in an Online Labor Marketplace," Proceedings of the ACM on Human-Computer Interaction (CSCW), 2018.
[17] E. Gomez-Herrera, F. Müller-Langer, "Is There a Gender Wage Gap in Online Labor Markets? Evidence from Over 250,000 Projects and 2.5 Million Wage Bill Proposals," CESifo Working Paper 7779, 2019.
[18] A. Dube, J. Jacobs, S. Naidu, et al., "Monopsony in Online Labor Markets," American Economic Review: Insights, 2020.
[19] G. Sharma, "Monopsony and Gender," Working Paper, MIT, 2023.
[20] A. Agrawal, N. Lacetera, E. Lyons, "Does Standardized Information in Online Markets Disproportionately Benefit Job Applicants from Less Developed Countries?," Journal of International Economics, 2016.
[21] A. Pallais, "Inefficient Hiring in Entry-Level Labor Markets," American Economic Review, 2014.
[22] M. Graham, I. Hjorth, V. Lehdonvirta, "Digital Labour and Development: Impacts of Global Digital Labour Platforms and the Gig Economy on Worker Livelihoods," Transfer: European Review of Labour and Research, 2017.
[23] A. J. Wood, M. Graham, V. Lehdonvirta, et al., "Good Gig, Bad Gig: Autonomy and Algorithmic Control in the Global Gig Economy," Work, Employment and Society, 2019.
[24] R. Jensen, "Do Labor Market Opportunities Affect Young Women's Work and Family Decisions? Experimental Evidence from India," Quarterly Journal of Economics, 2012.
[25] L. Ho, S. Jalota, A. Karandikar, "Bringing Work Home: Flexible Arrangements as Gateway Jobs for Women in West Bengal," STEG Working Paper, 2024.
[26] M. Chopra, I. Medhi Thies, J. Pal, et al., "Exploring Crowdsourced Work in Low-Resource Settings," CHI, 2019.
[27] S. Jayachandran, "Social Norms as a Barrier to Women's Employment in Developing Countries," IMF Economic Review, 2021.
[28] M. Miceli, J. Posada, "The Data-Production Dispositif," Proceedings of the ACM on Human-Computer Interaction (CSCW), 2022.
[29] N. Sambasivan, R. Veeraraghavan, "The Deskilling of Domain Expertise in AI Development," CHI, 2022.
[30] J. Muldoon, C. Cant, M. Graham, et al., "The Poverty of Ethical AI: Impact Sourcing and AI Supply Chains," AI & Society, 2023.
[31] P. Tubaro, A. A. Casilli, M. Coville, "The Trainer, the Verifier, the Imitator: Three Ways in Which Human Platform Workers Support Artificial Intelligence," Big Data & Society, 2020.
[32] L. Irani, "Difference and Dependence among Digital Workers: The Case of Amazon Mechanical Turk," South Atlantic Quarterly, 2015.
[33] J. Posada, "The Coloniality of Data Work in Latin America," AAAI/ACM Conference on AI, Ethics, and Society (AIES), 2021.
[34] Fairwork, "Fairwork Cloudwork Ratings 2023: Work in the Planetary Labour Market," Fairwork, 2023.
