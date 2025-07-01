### Search Overview
A total of 10 Mendelian Randomization (MR) studies were identified through a search conducted using PubMed. These studies span from 2020 to 2025 and investigate various diseases related to mTOR-dependent protein levels.

### Data Sources for Instrument Selection
Most studies utilized the INTERVAL study dataset for genetic instrument selection, demonstrating a common reliance on this resource. Additional data sources included specialized consortia and datasets tailored to specific diseases; for example, the study by Zhang et al. (2023) utilized the International Multiple Sclerosis Genetics Consortium, while Soliman et al. (2020) used DIAGRAM for diabetes-related data.

Mu et al. (2023) and Cheng et al. (2023) drew from the INTERVAL and the Integrative Epidemiology Unit (IEU) GWAS database, while the latter also included GEFOS for osteoporosis associations. Yan et al. (2024), Cai et al. (2022), and Ying et al. (2024) incorporated FinnGen, a robust source for broader epidemiological insights. Studies like Wang et al. (2025) also used the Global Lipids Genetics Consortium, highlighting a combined approach with computational and experimental methods.

### Differences in QTL Targets
All studies consistently targeted rapamycin-associated proteins; still, the molecular targets within mTOR pathways varied slightly. Soliman et al. (2020), for example, also investigated EIF-4E and EIF-4A due to their relevance in type 2 diabetes. This additional focus adds depth, showcasing how targeting different aspects of mTOR pathways can yield a more comprehensive biological relevance.

### SNP Selection Criteria and LD Clumping Thresholds
The majority of studies applied a p-value threshold of 5×10^-6 for selecting SNPs, except for Zhang et al. (2023), who used a more lenient threshold of 1×10^-5. The strictest LD clumping threshold (r² = 0.001) was observed in studies by Mu et al. (2023), Cheng et al. (2023), Hong-Yan Cai et al. (2023), and Ying et al. (2024). On the other hand, Wang et al. (2025), Yan et al. (2024), and several others used a more relaxed threshold of r² = 0.05, potentially leading to different degrees of variant selection and inclusivity.

### Pleiotropy Checks and Sensitivity Analyses
For pleiotropy checks, all studies engaged essential corrections, predominantly MR-Egger for directional pleiotropy and Cochran’s Q for heterogeneity. The study by Wang et al. (2025) integrated MR-PRESSO for distortion testing. In contrast, standard MR-Egger and weighted median methods sufficed for most other papers, particularly the works by Mu et al. (2023) and Zhang et al. (2023). Cai et al. (2022, 2023) adhered to a moderately strict protocol but remained methodologically sound.

### Final Assessment of Study Quality and Reliability
Zetao Wang et al. (2025)'s study stands out due to its integration of multiple omics datasets, rigorous pleiotropy checks (including MR-PRESSO), and p < 1×10^-6 SNP selection criteria, signaling high methodological rigor. Mu et al. (2023) and Cheng et al. (2023) also demonstrated robustness with stringent r² thresholds and consistent datasets but are slightly less comprehensive in pleiotropy measures compared to Wang et al. (2025).

Conversely, Zhang et al. (2023) exhibited a more lenient SNP threshold and was limited in pleiotropy checks, thereby representing a relatively weaker study. The study by Soliman et al. (2020) was robust in its multi-target approach but did not exceed the methodological depth shown by Wang et al. (2025).

**Recommended Benchmarks for Future Studies:**
1. **Wang et al. (2025)** for its comprehensive omics integration and rigorous analytical robustness.
2. **Mu et al. (2023)** for stringent SNP selection and consistency across datasets, offering high reliability in genetic instrument selection and validation.