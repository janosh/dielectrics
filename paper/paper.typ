#import "template.typ": (
  arkheion,
  arkheion-appendices,
  pdf-img,
  si0,
  si1,
  si4,
  subfigure,
)
// https://github.com/schang412/typst-whalogen
// ce(str) used to render chemical formulas
#import "@preview/whalogen:0.3.0": ce

#let CTTO = ce("CsTaTeO6")
#let BZO = ce("Bi2Zr2O7")

#let pyproject = toml(read("../pyproject.toml", encoding: none))
#let citation = yaml(read("../citation.cff", encoding: none))
#let authors = (
  citation.authors.map(author => (
    name: author.given-names + " " + author.family-names,
    orcid: author.orcid,
    affiliation: author.affiliation,
    email: if author.keys().contains("email") { author.email } else { none },
  ))
)

#show: arkheion.with(
  title: citation.title + ": " + citation.subtitle,
  authors: authors,
  abstract: [
    Materials with high-dielectric constant easily polarize under external electric fields, allowing them to perform essential functions in many modern electronic devices.
    Their practical utility is determined by two conflicting properties: high dielectric constants tend to occur in materials with narrow band gaps, limiting the operating voltage before dielectric breakdown.
    We present a high-throughput workflow that combines element substitution, ML pre-screening, ab initio simulation and human-in-the-loop filtering to efficiently explore the vast space of unknown materials for potential dielectrics, leading to the synthesis and characterization of two novel dielectric materials, #CTTO and #BZO.
    This work constitutes a successful demonstration of ML-guided multi-objective materials screening reporting the first high-purity synthesis and dielectric characterization of #BZO with a band gap of 2.27 eV and a permittivity of 20.5, meeting all target metrics of our multi-objective search.
    The second synthesized candidate, #CTTO, was a structure generated via element substitution not present in our reference data sources, thus exemplifying successful de-novo materials design of a thermodynamically stable material.
    However, unfortunately, the low observed bandgap of 1.05 eV renders #CTTO unusable as a dielectric material.
    We believe our successful synthesis results highlight both the potential and current limitations of applying ML in materials discovery.
    We emphasize the wider need for experimental validation of ML predictions to better understand and address limitations in high-throughput databases powering ML models for computational material science.
  ],
  keywords: pad(right: 8em, pyproject.at("project").at("keywords").join(" · ")),
  date: citation.date-released, // date of arXiv submission
)

#place(
  right,
  dy: -8em,
  float: false,
  [
    #place(dx: -4.8em, dy: 5em, rotate(-90deg)[Graphical Abstract])
    #pdf-img("figs/drawio/discovery-funnel.pdf", width: 7em)
  ],
)

= Introduction
<sec:introduction>

Dielectric materials are indispensable in numerous modern electronic devices including central processing units (CPUs), random access memory (RAM), solid-state disks (SSDs), high-frequency (5G) antennas, photovoltaics, and light-emitting diodes (LEDs) @wang_high_2018 @ponceortiz_highk_2010. Their utility hinges on the intricate balance between dielectric constant and band gap, two anti-correlated properties that rarely co-occur in a single material. High band gaps are crucial for reducing leakage current and preventing dielectric breakdown when subjected to high voltage. Conversely, a large dielectric constant is desirable for minimizing the energy required for polarization, which is especially important in applications like transistor gates. As transistors continue to shrink, the need for materials that can serve as ultra-thin gate dielectrics while withstanding operating voltages grows.

Historically, the discovery of dielectric materials has often relied on trial and error. Recent advancements, particularly in automated workflows for computational screening using density functional perturbation theory (DFPT) have shown promise in systematically searching for high-performance dielectrics, e.g. mapping the bandgap-dielectric Pareto front of binary and ternary oxides @yim_novel_2015. Improvements in compute power and workflow robustness have since enabled the scaling to several thousand diverse materials @petousis_high-throughput_2017 @petretto_highthroughput_2018 @choudhary_highthroughput_2020.

However, the sheer size of the space of $tilde 10^5$ known, let alone the $tilde 10^(10)$ hypothesized materials (up to quaternary order) @davies_computational_2016, prohibits sampling without inductive bias and presents a daunting challenge for existing computational methods. Consequently, the dielectric properties of the vast majority of the $tilde 10^7$ simulated inorganic crystals remain unknown, making it likely a more comprehensive exploration of the space should yield novel high-performance materials. To screen even a small subset of the full space requires orders of magnitude cheaper methods. Worse, to go beyond the $tilde 10^5$ known materials introduces another layer of computational complexity in the form of thermodynamic stability prediction on top of estimating band gap and dielectric constant.

To address this, we propose a new dielectric discovery workflow that judiciously integrates machine learning (ML) as the first filter in a multi-step funnel. ML, while less reliable than traditional methods like DFPT, is orders of magnitude faster and quickly improving in accuracy. Our ML-guided approach uses surrogate models for band gaps, dielectric constants, and formation energies. Instead of exact Cartesian coordinates, we employ Wyckoff positions for a coordinate-free, coarse-grained crystal structure representation @goodall_rapid_2022. This enables rapid generation and stability prediction of novel structures through elemental substitutions. Following DFPT validation of the most promising candidates, the last selection step is an expert committee to incorporate human intuition when weighing the risks, precursor availability and ease of experimental synthesis of all high-expected-reward materials. Finally, we validate the whole workflow by deploying it from start to finish which culminated in making and characterizing two new metastable materials in the process: #CTTO and #BZO which partially and fully satisfy our target metrics, respectively.

Finding exceptional materials that extremize a single property necessarily requires extrapolation from the training data, for example maximizing hardness @zhang_finding_2021 @zuo_accelerating_2021 @schmidt_machinelearningassisted_2023. This is fundamentally at odds with the statistical nature of ML, leading to increased error and less reliable predictions. Our approach diverges from previous efforts by choosing a target class of materials where the path to application relevance requires balancing multiple conflicting properties. This was driven by the hypothesis that doing so may allow the ML models to operate within regions of good training support while still predicting materials with exceptional figures of merit. This type of tradeoff is ubiquitous in material science and is seen in other materials classes such as thermoelectrics (need high low thermal but high electrical conductivity) @gaultois_perspective_2016 @yan_material_2015, catalysts (need high activity for fast reactions which tends to lower selectivity, increasing unwanted side reactions) @guan_bimetallic_2021 @liutkova_ca_2023, high-strength and shape-memory alloys (need high strength and high ductility) @chiu_investigations_2022 @li_effect_2021, and many more.

Despite a nascent but growing body of work on automated and high-throughput synthesis @king_rise_2011 @bedard_reconfigurable_2018 @steiner_organic_2019 @burger_mobile_2020 @szymanski_autonomous_2023 @lunt_modular_2024, experimental validation remains a key bottleneck in the design of materials. The process of manually developing experimental synthesis recipes for theoretical materials is very time-consuming, often taking months to a year per material. The central claim of ML-guided screening and related efforts in rational materials design is that we can reduce the downside risk of attempting novel synthesis procedures by increasing the hit rate of successful materials. To test the performance of our ML-guided approach we developed synthesis procedures for two materials predicted to be high-performing - #CTTO and #BZO, with the structure of #CTTO created by our generative workflow. Both materials displayed dielectric character with measured permittivities in the 43rd and 81st percentile, respectively, of 136 experimental reference results for dielectric materials reported in @petousis_high-throughput_2017 @petousis_benchmarking_2016, validating the benefits of our ML-guided workflow.

In summary, our work showcases an advancement in ML-guided materials discovery, demonstrating its potential in efficiently navigating the vast landscape of dielectric materials and balancing multiple material properties for optimal device performance.

= Results
<sec:results>
We first report the computational output of our workflow and then present experimental validation of two novel dielectric materials, #CTTO and #BZO.

== A scalable machine learning workflow for dielectric discovery
<sec:ml-workflow-for-dielectric-discovery>

#figure(
  pdf-img("figs/drawio/discovery-workflow-build-step-5.pdf"),
  caption: [
    Diagram of our dielectric material discovery workflow, integrating ML pre-screening and elemental substitution for generating novel crystals with high-throughput DFPT validation. The discovery pipeline can operate in two modes: screening and generation. Screening mode searches for large permittivity among known materials. In generation mode, we feed the top 1k MP structures by figure of merit $Phi_"M"$ into an element substitution process.
  ],
)<fig:discovery-workflow>

This section describes the components and design decisions of our dielectric discovery workflow visualized in @fig:discovery-workflow.

The large search space and high cost of experimental validation demand a funnel approach to dielectric materials discovery. To maximize the size of the initial candidate pool and still retain tractable computational cost, less auspicious materials must be discarded by a hierarchy of successively more expensive but higher-fidelity computational filters. Such an approach maximizes return on invested effort by allotting more resources to candidates which accumulated evidence of expected utility in earlier filters. Our proposed implementation for such a funnel workflow depicted in @fig:discovery-workflow precedes high-throughput DFPT with 5-6 orders of magnitude cheaper ML pre-screening to reduce a large list of 131685 candidate materials down to 2532 with computed dielectric properties.

We pre-screen based on 4 quantities - thermodynamic stability derived from predicted formation energy $E_"form"$, band gap $E_"gap"$, ionic permittivity $epsilon_0$ and electronic permittivity $epsilon_oo$ - each of which is predicted by a separate ensemble of 10 Wren models @goodall_rapid_2022 independently trained from random initializations. This allows us to both massively expand the search pool of initial candidates and waste fewer resources on unpromising compounds. The formation energy and band gap training sets each consist of 319601 data points, the combination of 98850 Materials Project (MP) @jain_commentary_2013 calculations and 220751 from the WBM dataset @wang_predicting_2021 (named WBM from the author's last name initials) which was generated with MP-compatible VASP settings. The $epsilon_0$ and $epsilon_oo$ ensembles are trained on the much smaller dataset of #link("https://materialsproject.org/materials?has_props=dielectric")[7172 DFPT calculations in MP] (database version 2020-09-08) due to the lack of additional MP-compatible dielectric datasets.

While simply screening materials within large ab-initio databases for which properties of interest have yet to be calculated is a viable strategy, it is also important to demonstrate the generative capabilities of ML-based workflows. To this end, we identify the top 1k MP structures by figure of merit $Phi_"M" = epsilon_"tot" dot E_"gap PBE"$ and use them as seed crystals for element substitution. The expectation is that this generates novel structures with increased likelihood of high $Phi_"M"$. The substitution process involves replacing all sites of one element in the structure with a chemically similar element (e.g. #ce("Na") → #ce("K")), as determined by a similarity matrix mined from the ICSD @bergerhoff_inorganic_1983. After filtering out duplicates (compositions that already exist in MP or WBM, i.e. we do not consider structural degrees of freedom) as well as compounds containing noble gases, lanthanides or actinides, we are left with 131685 potential new dielectric materials.

Using the trained Wren ensembles, we predict $E_"form"$, $E_"gap"$, $epsilon_"ionic"$ and $epsilon_"elec"$ for all candidates, both those sourced from high-throughput databases and those produced using our generative methodology. We estimate the convex hull distance for each crystal from these predicted energies and discard those more than #si4[0.1eV/atom] above the hull. This is motivated by the observation that 90% of crystals in ICSD are predicted to be less than #si4[0.067eV/atom] above the convex hull @sun_thermodynamic_2016. This tolerance towards instability accounts for errors in DFT energies and the fact that some thermodynamically unstable materials are kinetically or entropically meta-stable and hence synthesizable.

The remaining candidates are ranked by their ML-predicted figure of merit $Phi_"M"^"Wren"$ and subjected to a high-throughput DFPT workflow as our computational budget permits, resulting in a database of 2532 dielectric properties.

== Computational discovery of dielectrics beyond the Pareto front
<sec:computational-results>
The violin plot in @fig:our-diel-elec-vs-ionic-violin shows Gaussian kernel density estimates (KDE) of all 2532 DFPT-computed electronic and ionic dielectric constants split by crystal system. Unlike the electronic contribution which is lower-bounded by the vacuum permittivity, the ionic dielectric constant can be zero in all crystal systems. We observe a general trend of higher dielectric constant the higher the crystal symmetry, especially for the ionic contribution. Only cubic crystals reach significant electronic permittivity with a median of 10.

#figure(
  pdf-img("figs/our-diel-elec-vs-ionic-violin.pdf", width: 97.0%),
  caption: [
    Violin plot showing Gaussian KDEs of DFPT-computed electronic (blue left halves) and ionic (orange right halves) contributions to the dielectric constant split by crystal system. The dashed horizontal lines in each violin show the median. Below each crystal system is the number of materials we have for it as well as its share of the total DFPT dataset in percent. The colored bold numbers (blue = low, red = high) show the mean of the top 30 electronic/ionic dielectric constants for each crystal system.
  ],
)<fig:our-diel-elec-vs-ionic-violin>

@fig:pareto-us-vs-qu-vs-petousis compares the results from our methodology against those published in Petousis et al. @petousis_high-throughput_2017 and Qu et al. @qu_high_2020 by plotting the PBE band gap on the $y$-axis against the total dielectric constant on the $x$-axis on a log-log scale. The blue circles show the 2532 DFPT results we computed. The 441 orange diamonds show data generated by @qu_high_2020 while the 139 green squares are from @petousis_high-throughput_2017. The dark blue dashed isolines indicate constant figure of merit at values $Phi_"M" = E_"gap" dot epsilon_"tot" = c in { 30, 60, 120, 240 }$ for band gap $E_"gap"$ and total dielectric constant $epsilon_"tot"$. Our results achieve a larger number of materials beyond the highest $Phi_"M"$ isoline of 240 than both previous works combined. We also achieve a higher hit rate per DFPT calculation of such high-merit materials as shown in @tab:hit-rate-comparison. For #cite(<qu_high_2020>, form: "prose") $15 \/ 441 = 3.4 %$ of materials achieve $Phi_"M" > 240$ , while #cite(<petousis_high-throughput_2017>, form: "prose") reach $7 \/ 139 = 5.0 %$ and our data has $155 \/ 2680 = 5.8 %$ materials with $Phi_"M" > 240$. Note that our hit rate increases even further when post-hoc excluding metals, i.e. filtering the hit rate analysis for materials with a band gap of at least #si4[0.1eV]. While the other works started from DFT structures with known band gaps and hence were able to filter out metals from the outset, the same is not possible when generating novel crystals with unknown electronic structures. Our workflow instead relies on ML band gap prediction to filter out metals. This step unfortunately suffers from a high false positive rate (metals misclassified as semiconductors/insulators). Thus by upgrading to a better band gap model, a future realization of our workflow could achieve a high-merit hit rate in excess of $154 \/ 1911 = 7.5 %$.

#figure(
  align(center)[#table(
      columns: 3,
      align: (left, center, center),
      table.header([Study], [Number of Hits / Total], [Hit Rate (%)]),
      table.hline(),
      [Petousis et al. @petousis_high-throughput_2017], [$7 \/ 139$], [$5.0$],
      [Qu et al. @qu_high_2020], [$15 \/ 441$], [$3.4$],
      [This work], [$155 \/ 2532$], [5.8],
      [This work (with $E_"gap" > 0.1$ eV)], [$154 \/ 1911$], [$bold("7.5")$],
    )],
  caption: [Hit rate comparison for materials with $Phi_"M" > 240$. Excluding metals misclassified as insulators by our band gap models (which did not enter the other works in the first place), we achieve a $Phi_"M" > 240$ hit rate of 7.5%. This validates our approach of creating candidate structures from known dielectrics and pre-screening with ML.],
  kind: table,
)<tab:hit-rate-comparison>

@fig:pareto-us-vs-qu-vs-petousis compares our DFPT data to the results of #cite(<petousis_high-throughput_2017>, form: "prose") and #cite(<qu_high_2020>, form: "prose"). Our workflow generates more high-$Phi_"M"$ materials than both previous works combined and at a higher hit rate per expensive DFPT calculation than either #cite(<petousis_high-throughput_2017>, form: "prose") or #cite(<qu_high_2020>, form: "prose"). We believe this hit rate increase is attributable to ML pre-screening and substituting elements into known dielectric materials.

#figure(
  pdf-img("figs/pareto-us-vs-petousis-vs-qu-plotly.pdf", width: 80.0%),
  caption: [
    Log-log plot of PBE band gap $E_"gap"$ vs. total dielectric constant $epsilon_"tot"$ visualizing the hit rates for high-$Phi_"M"$ materials from different studies. Many of our DFPT data points (blue circles) reach into regions far beyond the #si4[240eV] isoline. The orange diamonds and green squares show results from #cite(<petousis_high-throughput_2017>, form: "prose") and #cite(<qu_high_2020>, form: "prose") which produce fewer $Phi_"M" > 240$ materials, both in absolute numbers and as a fraction of dataset size (see @tab:hit-rate-comparison. The dark blue lines indicate constant figure of merit $Phi_"M" = E_"gap" dot epsilon_"tot"$. The stacked marginal rugs along the top and right show the distribution of band gaps and dielectric constants in each dataset.
  ],
)<fig:pareto-us-vs-qu-vs-petousis>

== Prospective Experimental Validation
<sec:experimental-results>
To validate our workflow's ability to produce viable dielectric materials in practice, we selected #CTTO and #BZO for experimental synthesis and characterization. Our selection criteria incorporated DFPT results, prior literature or related materials appearing in the ICSD @zagorac_recent_2019, as well as precursor availability and expected ease of synthesis. The selection process was facilitated by a custom web interface to visualize DFPT results on the Pareto front hooked up to a shared database for note-taking and collecting prior literature appearances on individual candidate materials detailed in @sec:web-interface. Even so, making #CTTO and #BZO required several trial-and-error iterations to optimize the synthesis conditions which we detail in this section.

=== Optimization and Purity
<sec:optimization-and-purity>

#figure(
  grid(
    columns: (1.4fr, 1fr, 1fr),
    column-gutter: 9pt,
    row-gutter: 3pt,
    align: (left, center, right),
    subfigure(
      pdf-img("figs/exp-rietveld-CsTaTeO6-Fd3m.pdf"),
      caption: [
        Pyrochlore Fd3m Rietveld fit for
      ],
      label: <fig:exp-rietveld-CsTaTeO6-Fd3m>,
    ),
    subfigure(
      image("figs/crystals/exp/CsTaTeO6-whole-cell.png", width: 17em),
      caption: [
        structural model
      ],
      label: <fig:CsTaTeO6-whole-cell>,
    ),
    stack(
      dir: ttb,
      subfigure(
        image("figs/crystals/exp/CsTaTeO6-a-site.png", width: 6em),
        caption: [
          Pyrochl. A site
        ],
        label: <fig:CsTaTeO6-a-site>,
      ),
      subfigure(
        image("figs/crystals/exp/CsTaTeO6-b-site.png", width: 6em),
        caption: [
          Pyrochl. B site
        ],
        label: <fig:CsTaTeO6-b-site>,
      ),
    ),

    subfigure(
      pdf-img("figs/exp-rietveld-Bi2Zr2O7-Fm3m.pdf"),
      caption: [
        Fluorite Fm3m Rietveld fit for
      ],
      label: <fig:exp-rietveld-Bi2Zr2O7-Fm3m>,
    ),
    subfigure(
      image("figs/crystals/exp/Bi2Zr2O7-whole-cell.png", width: 13em),
      caption: [
        structural model
      ],
      label: <fig:Bi2Zr2O7-whole-cell>,
    ),
    subfigure(
      image("figs/crystals/exp/Bi2Zr2O7-polyhedra.png", width: 15em),
      caption: [
        Isolated #ce("Zr/BiO8") polyhedra
      ],
      label: <fig:Bi2Zr2O7-polyhedra>,
    ),
  ),
  gap: 2em,
  caption: [
    Structural determination of #CTTO and #BZO (#link("https://materialsproject.org/materials/mp-756175")[mp-756175]) using XRD and Rietveld refinement. $Q = 2 pi dot d^(- 1) [Å^(-1)]$ is the scattering vector. @fig:CsTaTeO6-whole-cell Crystal structure of the best Rietveld fit for #CTTO with @fig:CsTaTeO6-a-site and @fig:CsTaTeO6-b-site showing the defect-pyrochlore A and B site octahedra. @fig:Bi2Zr2O7-whole-cell Crystal structure of the best Rietveld fit for #BZO with @fig:Bi2Zr2O7-polyhedra showing the isolated #ce("Zr/BiO8") polyhedra.
    Notable impurities were detected in the XRD scan @fig:exp-rietveld-CsTaTeO6-Fd3m. #CTTO has many $h k l$ reflections, most of which are not distinguishable from the background noise. The most prominent observable peak at $Q = 1.7$ as marked by the orange arrow. The absence of a (111) peak in the Rietveld fit @fig:exp-rietveld-Bi2Zr2O7-Fm3m suggests a defect-fluorite structure with one oxygen vacancy, in contrast to the literature-proposed pyrochlore model.
  ],
)<fig:exp-structure-determination>

#figure(
  grid(
    columns: (1fr, 1fr),
    row-gutter: 9pt,
    column-gutter: 9pt,
    subfigure(
      pdf-img("figs/exp-diffuse-reflectance.pdf"),
      caption: [
        Diffuse reflectance spectra
      ],
      label: <fig:exp-diffuse-reflectance>,
    ),
    subfigure(
      pdf-img("figs/exp-tauc-bandgaps.pdf"),
      caption: [
        Optical band gap from Tauc
      ],
      label: <fig:exp-tauc-bandgaps>,
    ),

    subfigure(
      [#pdf-img("figs/exp-CsTaTeO6-diel-real-imag-loss-vs-freq.pdf")
        #place(
          dx: 13.2em,
          dy: -10.8em,
          image(
            "figs/exp-CsTaTeO6-diel-real-imag-loss-vs-freq-inset.png",
            width: 30.0%,
          ),
        )
      ],
      caption: [
        dielectric response vs frequency
      ],
      label: <fig:exp-CSTaTeO6-diel-real-imag-loss-vs-freq>,
    ),
    subfigure(
      pdf-img("figs/exp-Bi2Zr2O7-diel-real-imag-loss-vs-freq.pdf"),
      caption: [
        dielectric response vs frequency
      ],
      label: <fig:exp-Bi2Zr2O7-diel-real-imag-loss-vs-freq>,
    ),
  ),
  caption: [
    Dielectric measurements of #BZO and #CTTO. @fig:exp-diffuse-reflectance Diffuse reflectance spectra for both compounds exhibit distinctive absorption edges, indicating ordered crystalline structures. @fig:exp-tauc-bandgaps Tauc plot measuring absorption coefficient $alpha(E_"ph")$ vs photon energy $E_"ph" = h nu$ for both compounds.The extracted optical band gaps are $E_"gap" = #si4[2.27eV]$ for #BZO and #si4[1.05eV] for #CTTO. @fig:exp-CSTaTeO6-diel-real-imag-loss-vs-freq Dielectric response of #CTTO as a function of frequency. We measure $epsilon_"tot" = 26$ at #si4[1MHz] electric field (compared to 67 from DFPT) Its unwelcome high dielectric loss of $tan(delta) = 0.23$ at #si4[1MHz] confirms the semiconducting nature observed in the Tauc plot's spectroscopic data. @fig:exp-Bi2Zr2O7-diel-real-imag-loss-vs-freq Dielectric response of #BZO as a function of frequency yields $epsilon_"tot" = 20.5$ at #si4[1MHz] (compared to 206 from DFPT) We highlight #BZO's dielectric loss of less than 0.1 above 1~kHz, a sufficiently low value for many practical applications.
  ],
)<fig:exp-diel-characterization>

We use X-ray diffraction (XRD) data and Rietveld fits to test our structural models for #CTTO and #BZO.

The measured XRD pattern for our sample at 80% of the theoretical weight density readily fits a defect-pyrochlore model. The atomic displacement parameters were small but positive within error. Even though multiple disordered models were explored, the defect-pyrochlore provided the best fit. We detected impurities constituting $4.20 plus.minus 0.12$ % of total weight that are highlighted in @fig:exp-rietveld-CsTaTeO6-Fd3m.

For #BZO, we explored optimal synthesis temperatures between #si4[550°C] -- #si4[750°C]. An extensive 8-hour XRD scan of after 48~h of heating at 650~°C confirmed the absence of and impurities in the sample, which significantly surpasses existing literature in terms of purity @pandey_metastable_2018. After sintering, we obtained a ceramic sample with 92+% of the theoretical density of a single crystal. Contrary to literature reports that typically describe an impure pyrochlore with a noticeable (111) reflection @pandey_metastable_2018, our samples exhibit no such peaks. Prolonged heating did result in a broad (111) peak but was accompanied by undesired and impurities. Avoiding prolonged heat, the Rietveld analysis in @fig:exp-rietveld-Bi2Zr2O7-Fm3m shows the (111) peak to be absent, favoring a defect-fluorite model for , in contrast to the literature-proposed pyrochlore models. The compound exhibited large atomic displacement parameters ($B_"iso"$) which may arise from two superimposed crystallographic positions or due to off-stoichiometry (occupancy). Both commonly result in models with large atomic displacement parameters that simulate the distribution of electron density from these sites. However, attempts to reduce atomic displacement using site splitting and occupancy refinement for disordered materials did not yield better fits. Higher-quality diffraction data, e.g. from neutron scattering, would likely be required for more accurate modeling.

Further details on synthesis development, equipment used and XRD fitting for both #CTTO and #BZO are provided in methods @sec:synthesis-details and @sec:Bi2Zr2O7-synthesis-development and @sec:CsTaTeO6-synthesis-development.

=== Dielectric Characterization
<sec:dielectric-characterization>

Having selected, synthesized at high purity, and confirmed the structures of #CTTO and #BZO, we investigate their physical properties. The band gaps of both materials were identified using UV-vis impedance spectroscopy on powders using diffuse reflectance and an integrating sphere. These data can be seen in @fig:exp-diffuse-reflectance and they were modified and fit using the Kubelka Munk @kubelka_article_1931 equation to extract the bandgap, seen in @fig:exp-tauc-bandgaps. @fig:exp-diffuse-reflectance shows diffuse reflectance measurements for #CTTO and #BZO exhibiting distinctive absorption edges. The extracted band gaps are #si4[2.27eV] for #BZO and #si4[1.05eV] for #CTTO. It is worth noting that the measurements for both #CTTO and #BZO turned out much lower than the DFT-calculated values of #si4[2.09eV] and #si4[2.96eV] respectively. This is surprising given PBE's tendency to underestimate experimental band gaps. For #CTTO, this may be due to complex defect effects not captured by DFT arising from #ce("Cs") or #ce("Te") volatility @weiss_photoinduced_2020. A more accurate ML band gap model that provides a more specific filter for metals and semiconductors would save future implementations of our workflow from spending unwarranted compute and lab time on semiconducting compounds like #CTTO. However, given the limitations of PBE observed for these materials it would be advisable to train the model on reference data obtained from higher levels of theory.

The low value of $E_"gap" = #si4[1.05eV]$ for #CTTO is consistent with its observed black color and unfortunately renders it unusable as a dielectric material. The dielectric measurements in @fig:exp-CSTaTeO6-diel-real-imag-loss-vs-freq confirm a band gap-related high dielectric loss#footnote[The dielectric loss measures dissipation of electromagnetic energy propagating inside a dielectric material to heat. It is defined as the phasor in the complex plane between the real resistive (lossy) and imaginary reactive (lossless) components of the relative permittivity $epsilon_"rel" = epsilon_"real" + i epsilon_"imag"$ and is commonly given as the tangent of that angle, $tan(delta) = epsilon_"imag" / epsilon_"real"$]. It is worth noting that despite its low band gap, #CTTO exhibits high polarizability of $epsilon_"real" = 26$ at #si4[1MHz] up to its low breakdown voltage. However, its high dielectric loss of $tan(delta) = 0.23$ at #si4[1MHz] confirms the semiconducting behavior observed in the spectroscopic data. We also caveat the measured dielectric constant with the fact that 23% loss makes the extracted $epsilon_"real"$ value less reliable.

The compound #BZO has an observed band gap of #si4[2.27eV], making it a useful dielectric. Importantly, the observed band gap is #si4[0.27eV] (12.5%) higher than the previously reported mixed phase @pandey_metastable_2018 who report $E_"gap" = #si4[2eV]$. This suggests reduced defect states and further substantiates the high purity and distinct phase of our synthesized materials. Dense ceramics were only accessible using spark plasma sintering, due to the metastable nature of the compound. Room temperature dielectric properties as a function of frequency can be seen in @fig:exp-Bi2Zr2O7-diel-real-imag-loss-vs-freq. Dielectric properties arise from a variety of different mechanisms: space charge, dipolar, ionic, and electronic polarization. Measuring as a function of frequency allows mechanisms with slower response times, such as space charge polarization arising from ionic conductivity, to be isolated from more meaningful mechanisms. At high frequency (#si4[1MHz]) the dielectric response shows a dielectric permittivity ($epsilon_"real"$) of 44 and a dielectric loss of $tan(delta) = 0.018$. The low dielectric loss (\<0.1) indicates that the value of $epsilon_"real"$ is free from conductive contributions. The permittivity of 44 is similar to doped #ce("Bi2O3") with fluorite-related structures, such as a 10%-doped #ce("Ta^5+") with a $epsilon_"real"$ of 42 @valant_dielectric_2004. However, #BZO has a higher $epsilon_"real"$ than #ce("HfO2") or #ce("ZrO2") ($epsilon_"real"$ between 22-25) fluorites which are used as high-k dielectrics industrially @choi_development_2011, making it a worthwhile material to consider for real-world application. Furthermore, the aqueous-based synthesis with low calcination temperature of #BZO presents promising opportunities for solution processing of dielectrics which are compatible with existing industrial MOSFET processing technologies.

= Methods
<sec:methods>

== Derivation of $Phi_"M"$
<sec:choosing-fom>


Since dielectric constant and band gap are both crucial factors when considering electronic device applications, we measure materials by a figure of merit defined as
$
  Phi_"M" = E_"gap" dot epsilon_"tot" #h(2em) "where" #h(2em) epsilon_"tot" = epsilon_"ionic" + epsilon_"elec".
$<eq:fom>
A product ensures materials exhibit at least intermediate levels of band gap _and_ permittivity. This follows #cite(<yeo_mosfet_2003>, form: "prose") who define this semi-empirical expression for the leakage current through a MOSFET gate dielectric:
$
  J_G prop thin exp {- frac(4 pi sqrt(2 q), h) dot (m_"eff" med Phi_b)^(1 \/ 2) epsilon_"tot" dot t_"ox,eq"}
$<eq:mosfet-leakage>
with charge $q$, effective tunneling mass $m_"eff"$ of the electron or hole, injection barrier of the gate dielectric $Phi_b$, and the #ce("SiO2")-equivalent-capacitance oxide thickness
$t_"ox,eq" = \(epsilon_ce("SiO2") \/ epsilon_"tot"\) dot t_"phys"$. Increasing $(m_"eff" med phi.alt_b )^(1\/2) epsilon_"tot"$ exponentially suppresses the tunneling current. Thus MOSFET device miniaturization requires materials that maximize this quantity. The effective tunneling mass $m_"eff"$ and the carrier injection barrier $phi.alt_b$ are expensive to compute from first principles and out of reach for high throughput workflows. #cite(<hinkle_novel_2004>, form: "prose") therefore approximate their product as proportional to the band gap, $E_"gap" prop ( m_"eff" phi.alt_b )^(1/2)$. Increasing $Phi_"M" = E_"gap" dot epsilon_"tot"$ should therefore result in exponentially suppressed tunneling current.

== Initial Candidate Generation
<sec:initial_candidate_generation>
As shown in @fig:discovery-workflow, we begin our discovery campaign by generating a large set of initial candidates. The Materials Project currently holds 7172 materials with DFPT-calculated permittivity. Starting with the 1000 highest FOM MP dielectric materials, we perform 1000 rounds of elemental substitution on each source structure. Substitutions are guided by a chemical similarity matrix @wang_predicting_2021 mined from the Inorganic Crystal Structure Database (ICSD) @bergerhoff_inorganic_1983, resulting in 1 million potential new structures.

The chemical similarity matrix offers a likelihood score for elemental substitution, based on their co-occurrence in the same space group in ICSD. This approach is inspired by previous works @glawe_optimal_2016@goodall_rapid_2022. During substitution, we swap out one element for another across the entire structure and limit ourselves to the 89 elements present in the Materials Project. This process yields 187,176 potential candidates, which we then filter as follows:

+ Remove duplicates: $10^6 → #si1[187176]$

+ Exclude structures containing rare earths (lanthanides and actinides): $#si1[187176] → #si1[133367]$

+ Exclude structures containing noble gases: $#si1[133367] → #si1[133241]$

+ Remove existing Materials Project compositions: $#si1[133241] → #si1[131685]$

We remove rare earths because DFT is well-known to struggle with the 4f electrons @soderlind_groundstate_2014, making any DFPT on such compounds less reliable. We filter noble gases because they are chemically inert and hence unlikely to occur in stable compounds. We remove structures with matching compositions in the Materials Project since many MP structures are sourced from the ICSD and hence the experimentally observed ground state. As such, any structures we generate with polymorphs in MP have an increased risk of being metastable at best.

== Training Data
<sec:training-data>

We trained the Wren ensembles for formation energy and band gap on the combination of two large datasets:

- The #strong[Materials Project (MP) database] @jain_commentary_2013 is a well-curated database of high-throughput DFT calculations. We used MP database version 2020-09-08 powered by `pymatgen` version 2022.0.8 containing 146,323 crystal structures @persson_materials_2022.

- Wang et al. @wang_predicting_2021 calculated energies and properties for a large number of crystal structures generated from MP source structures via elemental substitution with chemically similar elements as pioneered in @glawe_optimal_2016. After substitution, the structures were relaxed using MP-compatible workflows. Using the author's initials, we refer to this as the #strong[WBM data set]. After de-duplication and cleaning, WBM contains 220k structures.

Together, MP and WBM provide 319601 formation energies, 319601 band gaps. The Materials Project also contains dielectric properties for 7172 materials which we used to train Wren ensembles that predict ionic and electronic permittivity.

== Machine Learning

<sec:ml>
To predict formation energy, band gap and permittivity in the ML pre-filtering step for each of the 131,685 generated candidate materials (@sec:initial_candidate_generation), we utilize Wren ensembles @goodall_rapid_2022 which use a coarse-grained Wyckoff position-based material representation that discards exact atomic coordinates in favor of discrete, enumerable symmetry labels identifying groups of sites that map onto each other under the crystal's symmetry operations. Each Wyckoff position is embedded into a vector space and concatenated with the crystal site's Matscholar element embeddings @weston_named_2019 before being placed in a fully connected graph with all other Wyckoff sites. Each node in the graph is then allowed to contextualize to its neighbors via multiple message-passing layers and finally mean-pooled to get a permutation- and relaxation-invariant, fixed-length, symmetry-aware crystal descriptor which is much cheaper to obtain than relaxed atom positions. A simple feed-forward net with skip connections @he_deep_2015 and ReLU @nair_rectified_2010 activations then maps the Wren crystal embedding onto one or multiple target variables. This featurization becomes more informative with higher symmetry in the structure. For our use case of filtering out unrelaxed structures immediately after elemental substitution, its distinct advantage is invariance under structure relaxations as long as the relaxation does not affect the structure's symmetry (many DFT relaxations enforce keeping the initial symmetry throughout the relaxation, e.g. by setting $"ISYM" > 0$ for VASP).

For each of the four material properties of interest -- formation energy, ionic and electronic dielectric constants, and band gap -- we train Deep Ensembles @lakshminarayanan_simple_2016 of 10 independent Wren models. Trained on identical data but with different initializations, these ensembles offer two advantages:

- The ensemble average yields more reliable point estimates compared to single models.

- Ensemble variance allows us to assess epistemic model uncertainty, which we incorporate into a risk-aware figure of merit via error propagation. This reduces false positives at the cost of increased false negatives.

The ensemble-risk-aware figure of merit $Phi_"M"^"std-adj"$ including uncertainty propagation reads:
$
  Phi_"M"^"std-adj" = sqrt(( epsilon_"tot" dot sigma_(E_"gap") )^2 + ( E_"gap" dot sigma_(epsilon_"tot") )^2),
$ where $epsilon_"tot"^"Wren"$ and $sigma_(epsilon_"tot")$ are the Wren ensemble mean and standard deviation for the predicted total dielectric constant. Likewise $E_"gap"^"Wren"$ and $sigma_(E_"gap")$ are the ensemble mean/std. dev. for the Wren-predicted band gap. We use the $Phi_"M"^"std-adj"$ (rather than the standard $Phi_"M"$) to rank element substitution structures for priority when allocating compute budget for DFPT calculations.

Moreover, for the formation energy ensemble, we also estimate aleatoric uncertainty, i.e. uncertainty that is inherent to the data, by using a "robust" loss function. This loss requires changing the final output layer of each model to predict two numbers per sample. The loss function interprets the first number as the predicted mean and the second as predicted aleatoric uncertainty. This uncertainty enters the loss function as an attenuation term on the $L^p$ norm. This allows the model to deweight the loss on predictions it attributes higher uncertainty to at the cost of incurring a higher regularization penalty.

$
  cal(L) = 1 / N sum_(i=1)^N frac(1, 2 sigma(bold(x)_i)^2) norm(bold(y)_i - bold(f)(bold(x)_i))^2 + 1 / 2 log sigma(bold(x)_i)^2
$
where $bold(x)_i$ are the model inputs, $bold(y)_i$ the corresponding target value, $bold(f)(bold(x)_i)$ the model predictions and $sigma(bold(x)_i)$ is the observation noise parameter, the second predicted by the model. The observation noise is learned by the model as a function of the input, making the loss heteroscedastic (i.e. sample-dependent). Thus the model can learn to deweight the standard $L^2$ loss in the first term by increasing the predicted observation noise.

We do not set a robust loss on the other 3 ensembles due to an increase in validation error which we did not observe for the formation energy ensemble.

For all 4 Wren ensembles (formation energy, band gap, ionic + electronic dielectric constant), we adopt the same hyperparameters as @goodall_rapid_2022 to which we refer for details on the model architecture. In summary, each ensemble member consists of 3 message passing layers, each with a single attention head. Both parts of the soft-attention mechanism use single-hidden layers with 256 hidden units and LeakyReLU activation functions. The output network following the message-passing layers is a simple feed-forward net with skip connections and ReLU activation functions. Its 4 hidden layers have sizes 64, 256, 256, and 1, respectively.

== DFT Structure Relaxation
<sec:dft-structure-relaxation>
We used the Vienna ab-initio Simulation Package (VASP) @kresse_efficiency_1996@kresse_efficient_1996 in projector augmented wave (PAW) mode @blochl_projector_1994 to relax artificial crystal structures generated via elemental substitution of known structure prototypes. The exchange-correlation energy was computed in the generalized gradient approximation (GGA) @langreth_beyond_1983 using the Perdew-Burke-Ernzerhof (PBE) functional @perdew_rationale_1996. Input files were auto-generated by `pymatgen` @ong_python_2013. To perform high-throughput DFT, we used the Materials Project workflow library `atomate` @mathew_atomate_2017, the job launcher, queue manager and progress monitor Fireworks @jain_fireworks_2015, and the automatic error handler Custodian @ong_python_2013. Structures were relaxed until all interatomic forces fell below $10^(-2) thin$eV/Å and the total energy change between self-consistent field (SCF) cycles fell below $10^(-7) thin$eV.

== Dielectric Properties from DFPT
<sec:dfpt-to-dielectric>
Candidates that pass our ML filters are fed into high-throughput density functional perturbation theory (DFPT). This stage offers more accurate property estimates at 3-4 orders of magnitude increase in computational cost.

We computed the electronic permittivity using linear response theory at the generalized gradient approximation (GGA) level of density functional perturbation theory as implemented in VASP 6.2.0. High-throughput calculations were orchestrated on the Cambridge CSD3 cluster using the `wf_dielectric_constant` workflow in `atomate` v1.1.0 @mathew_atomate_2017. This yields Born effective charges and phonon modes at the $Gamma$ point @lee_comparative_2007.

We depart from standard MP dielectric settings in several respects. First, by using the (at the time) most recent `PBE_54` release of VASP POTPAW pseudopotentials (MP uses `PBE`). We used the default structure-dependent $k$-point grid as implemented in `pymatgen` which constructs Gamma-centered meshes for hexagonal and face-centered cells, and Monkhorst-Pack grids otherwise. However, we increased the grid density to 3000 $k$-points per atom despite the significant cost increase for a high-throughput workflow to accommodate the sensitivity of linear-response calculations to $k$-point sampling. We also set tight convergence criteria of `EDIFF` = $10^(-7) thin$eV (default = $10^(-5) thin$eV) and a high kinetic energy cutoff for the plane wave basis set of `ENCUT` = #si4[700eV] (default = #si4[520eV]). We expect these changes to increase the fidelity of our results, or at worst, increase compute cost at no benefit.

The total dielectric tensor splits into ionic ($epsilon^0$) and electronic ($epsilon^oo$) contributions:

$
  epsilon_(i j)^"total" = epsilon_(i j)^0 + epsilon_(i j)^oo
$
with $i, j in x, y, z$ the 3 spatial dimensions and 0 and $oo$ representing the electric field frequency. The ionic contribution $epsilon^0$ is computed from the Born effective charges $Z^(\*)$ and the phonon modes $omega$ @gonze_dynamical_1997,

$
  epsilon_(i j)^0 = frac(4 pi, Omega) sum_m frac(Z_(m, i)^(\*) Z_(m, j)^(\*), omega_m^2)
$
with $Omega$ the unit cell volume, $m$ the phonon mode index, $omega_m$ the infrared phonon frequency of mode $m$ and $Z_(m, i)^(\*)$ the $i$th component of the Born effective charge of mode $m$.

The scalar dielectric constant that enters our figure of merit equation @eq:fom[\[eq:fom\]] is the mean of the eigenvalues $epsilon_i$ of the total dielectric tensor:
$
  epsilon_"tot" = 1 / 3 sum_(i = 1)^3 epsilon_i^"total"
$
The ionic contribution $epsilon_"ionic"$ to the permittivity is known to be sensitive to low-frequency phonon modes which are incorrectly softened by the lattice parameter overestimation typical for GGA @yim_novel_2015, resulting in higher mean error than LDA. We chose to run GGA DFPT despite this known GGA shortcoming to retain compatibility with existing MP dielectric data @petousis_benchmarking_2016@petousis_high-throughput_2017.

== Web Interface for Collaborative Synthesis Selection
<sec:web-interface>

#figure(
  image("figs/plotly-web-app.png"),
  caption: [
    Screenshot of the #link("https://janosh.github.io/dielectrics")[web app] that aids with synthesis selection. The centerpiece of the app is an interactive scatter plot similar to @fig:pareto-us-vs-qu-vs-petousis showing the Pareto front of band gap and total dielectric constant. The legend on the right enables toggling between our own data set and data from prior works discussed in @sec:related-work. For our own data, we have legend groups for different calculation batches and $Phi_"M"$-based subsets of the data that allow switching between viewing ML predictions and/or their corresponding DFPT results with a third option to show a quiver plot that renders arrows between these points. This makes it easy to visualize how ML predictions differ from DFPT results and to look for trends in ML errors w.r.t. chemistry. Ellipses again indicate regions of particular interest for specific device applications (CPU, RAM, Flash storage). The density contours show lines of constant figure of merit.
  ],
)<fig:plotly-web-app>

The last step in our discovery workflow before experimental synthesis involves a custom-built web interface shown in @fig:plotly-web-app powered by a MongoDB Atlas M2 instance on the backend. This database is automatically updated when new `atomate` @mathew_atomate_2017 DFPT workflows finish on our compute cluster. To implement the frontend, we leveraged multiple open-source technologies:

- `pymongo` @fedorova_writes_2022 for fetching the latest calculation results from our `atomate` `tasks` collection.

- `plotly` powers the interactive scatter plot used to show computed and/or ML-predicted band gaps and dielectric constants, switch between different calculation series or best-of subslices of the data as well as clicking points to select individual materials for closer inspection.

- `CrystalToolkit` @horton_crystal_2023 renders the 3d structure of the material selected in the scatter plot with pan and zoom functionality.

- `dash` @hossain_visualization_2019 stitches the above 3 components together with callback functions. The two main ones are updating the structure viewer whenever a new point is selected from the scatter plot and updating the database when new free-form notes or categorizations are recorded in the text area and dropdown menu on the left.

In our case, selecting individual points from the scatter plot and annotating them with free-form text took place during remote live discussions between theorists and experimentalists while screen sharing. Since these meetings took place over months, the web app massively helped with keeping track of reasons for categorizing a given material as discarded or tentative/firm synthesis candidate or recording links to prior art for materials categorized as already confirmed dielectrics. Given this web app proved an enabler of effective remote collaboration between computational and experimental labs, we emphasize the importance of developing more custom tools that improve information flow and data visualization. Moreover, we found our tool significantly facilitates the process of keeping provenance. Ideally, this process should be automated entirely in the future as this area is extremely prone to human error.

The final verdict of these discussions results in a classification as one of

/ confirmed dielectric: prior experimental literature exists confirming our candidate material to be a dielectric. No point in synthesizing and re-characterizing, but increases trust in our workflow.

/ selected for synthesis: Promising in every way, i.e. high calculated band gap and permittivity, cheap and easily accessible precursors, synthesis procedure matches our experimentalists' area of expertise and has ideally been demonstrated in earlier experimental works but without dielectric characterization.

/ strong candidate: promising in some ways, i.e. high calculated band gap and permittivity but perhaps no existing literature reporting successful prior synthesis or compound looks challenging to make (e.g. might require aerobic environment)

/ weak candidate: less promising in terms of simulated properties but potentially easier to make than other materials with superior expected properties

/ discarded: failures of our screening method, usually due to existing literature indicating properties are not as we predict such as when a material was previously synthesized but reported as black, indicating a small band gap.

This interactive selection tool proved invaluable for extracting maximum utility and insight from the data we generated and resulted in identifying two candidates for final selection as suitable candidates for experimental synthesis.

We use GitHub Pages to host a figure-only version of this web interface at #link("https://janosh.github.io/dielectrics")[janosh.github.io/dielectrics]. It is set up with continuous integration to update automatically as new data is generated. It has no write access to the database and hence cannot be used to annotate or categorize candidate materials but serves as a user-friendly public entry point to the most promising results in our database that requires no setup nor technical knowledge to use.

== Synthesis Details
<sec:synthesis-details>
#CTTO was synthesized using standard solid-state synthesis techniques. Stoichiometric amounts of Cs2CO3 (Alfa Aesar, 99.95), #ce("Ta2O5") (Afla Asear, 99.999), and #ce("Te(OH)6") (Aldrich, 99.5) were added to an agate pestle and mortar and ground to homogenize the precursors before calcining at #si4[400°C] for #si4[24h] in an #ce("Al2O3") crucible. After calcining, samples were reground and pressed into a 10~mm disk and annealed at #si4[750°C] for #si4[48h] in a covered #ce("Al2O3") crucible to form the final product.

#BZO was synthesized using an ethylenediaminetetraacetic acid (EDTA) and nitrate chelation and combustion, similar to a sol-gel process, a reaction modified from @pandey_metastable_2018. Equal molar quantities of #ce("Bi2O3") and #ce("ZrO(NO3)2") were added to separate beakers and dissolved in minimal amounts of concentrated nitric acid by stirring with a magnetic stir bar. Once dissolved, these two solutions were mixed with a 4 times molar excess of EDTA to ensure chelation. The solution was then heated at #si4[80°C] until all liquid evaporated, leaving a brownish-white powder that was amorphous to X-rays. The amorphous powder was then calcined as a loose powder in a furnace inside a #ce("Al2O3") crucible at temperatures from #si4[550°C]--#si4[750°C] in #si4[50°C] increments for #si4[1h]. The samples heated at 650~°C produced the sharpest XRD peaks, without any trace of impurities. Samples heated higher than 650~°C or for longer than 1~h resulted in the decomposition of the sample into #ce("Bi2O3") and #ce("ZrO2"), indicating metastability.

Both samples were sintered using spark plasma sintering. Pure phase samples were loaded into #si4[10mm] graphite dies in a Thermal Technology LLC DCS10 furnace. Samples ($tilde$#si4[0.75g]) were loaded into a #si4[10mm] diameter graphite die lined with a graphite foil and loaded into a sample chamber which was evacuated and backfilled with #ce("He") three times. The sample was pressed uniaxially at #si4[60MPa], heated to the desired temperature at a rate of #si4[200°C/min], held for #si4[1min], and cooled at the same rate. The #CTTO sample was heated to a maximum temperature of #si4[750°C] and the #BZO sample was heated to #si4[600°C] resulting in samples with 92% and 94% of theoretical densities, respectively.

Diffuse reflectance measurements were taken on powdered #CTTO and #BZO using a Cary 5000 UV--Vis--NIR Spectrometer. Dielectric permittivity data was collected on sintered samples that had been thinned to a thickness of #si4[1mm] and sputtered with gold electrodes. Data was collected using an Agilent 4980A instrument with a home-built sample holder and a program created in LABVIEW. X-ray diffraction data was collected using a Paralytical X'pert Pro instrument with #ce("Co") K$alpha$1 ($lambda = #si4[1.788960Å]$) radiation. Rietveld analysis was carried out using Topas Academic on these X-ray data. Initial refinements started with parameters identified using the Pawley method. Final refinements included lattice parameters, atomic positions, atomic displacement parameters, profile parameters and the background.

= Discussion
<sec:discussion>
We have demonstrated a high-throughput workflow for dielectric materials discovery that combines data-driven and first-principles methods. We show in @tab:hit-rate-comparison that this combination achieves improved enrichment of high $Phi_"M"$ materials than ab-initio methods alone.

By deploying this workflow into practice, we identified and synthesized two candidate materials, #CTTO and #BZO. After careful Rietveld analysis to verify we realized the target structures, we measured their band gaps and dielectric properties. #BZO shows strong promise for electronic applications given its measured band gap of #si4[2.27~eV], dielectric constant of 20.5 and its relatively available constituent elements. #CTTO is a black semiconductor with a low band gap of #si4[1.05~eV] and dielectric constant of 26, making it unsuitable for electronic applications. However, we emphasize this structure was generated via element substitution by our workflow with no prior reports in the ICSD or MP. We thus demonstrated successful de novo synthesis on a challenging metastable phase and established a prior for the dielectric properties of similar materials in this largely unexplored region of chemical space. This outcome shows that ML-driven thermodynamic stability prediction has matured enough in reliability to be effectively incorporated into a complex multi-step workflow. This requires sufficient trust in the method to attempt a risky metastable synthesis in an unknown chemical system.

The biggest failure mode in our funnel search was the weakness of our band gap ML model. It incurred a high false-positive rate, predicting many generated metallic structures as semiconductors or insulators. Although there is significant room for improvement in ML band gap prediction, it was not the main focus of this work. We consider accurate band gap models to be an unsolved problem in materials informatics and encourage more efforts be directed at it. Models that predict a spectrum rather than a single scalar may be an interesting avenue to pursue. Predicting the electronic density of states (eDOS) like Mat2Spec @kong_density_2021 and inferring the band gap from that also opens the door to more nuanced loss functions and increased regularization during training. Sufficiently complex models with good inductive bias may learn more subtle trends from this approach. It should be noted, however, that Mat2Spec refrained from reporting band gaps inferred from their eDOS predictions, potentially indicating more work is required to unlock such benefits. #cite(<shoghi_molecules_2023>, form: "prose") @shoghi_molecules_2023 is a more recent work demonstrating impressive band gap accuracy on the matbench MP $E_"gap"$ task after pre-training on many large but non-cognate materials prediction tasks. This suggests that perhaps current model architectures and training methods can be sufficient. Achieving reliable ML band gap prediction could be a matter of careful data curation and model pre-training.

However, the challenge of predicting band gaps in our workflow is not restricted to ML but carries through to DFT. PBE exhibits an unusual severe overestimation ($E_"gap"^"PBE" > #si4[2.09eV]$) of the experimental band gap of #CTTO ($E_"gap"^"exp" = #si4[1.05eV]$). Although defect chemistry may play a role in this effect, there are obvious computing limitations in a high-throughput workflow, making the simulation of defect effects cost-prohibitive. One obvious improvement to narrow the gap between simulation and reality is to employ higher levels of theory such as r2SCAN or even to incorporate a third computational filter to the funnel in the form of hybrid functionals such as HSE, applied sparingly to compounds that have passed ML and PBE filters but before attempting experimental synthesis.

#heading(level: 1, numbering: none)[Code and Data Availability]
<sec:code-availability>

The MIT-licensed code for this work can be found at #link("https://github.com/janosh/dielectrics") and as a Zenodo archive at #link("https://doi.org/10.5281/zenodo.10456384"). Zenodo includes a complete dump of our DFPT dataset. Our live data is also publicly accessible through a MongoDB M2 Atlas instance with the schema of an `atomate` `tasks` collection. It can be queried free of charge and without registration using the read-only database credentials and example code snippet provided in the GitHub readme. This requires #link("https://pymongo.readthedocs.io")[`pymongo`] or any other MongoDB language driver. The query syntax will be familiar to users of the (legacy) Materials Project `MPRester` API. We used Materials Project data from the (#link("https://docs.materialsproject.org/changes/database-versions")[v2020.09.08];) database release and a cleaned version of the WBM dataset @wang_predicting_2021 available at #link("https://figshare.com/articles/dataset/22715158").

#heading(level: 1, numbering: none)[Acknowledgements]
<acknowledgements>
J.R. acknowledges support from the German Academic Scholarship Foundation (#link("https://wikipedia.org/wiki/Studienstiftung")[Studienstiftung];). A.A.L. acknowledges support from the Royal Society.

#heading(level: 1, numbering: none)[Supplementary Information]
<supplementary-information>
= Related Work
<sec:related-work>
While previous studies have made significant strides in automating high-throughput DFPT to uncover new dielectrics, our work diverges in 3 important regards. We prefix DFPT with generative and pre-filtering ML which allows us to consider a much larger initial candidate pool as well as venture into uncharted regions of material space in our search for high dielectrics. Using ML-preselection and biasing the structure generation to crystals similar in chemistry to known high dielectric materials in MP allows us to nonetheless maintain a higher hit rate of materials with high $Phi_"M" > 240$ than previous works as shown in @tab:hit-rate-comparison. Third, we built a web UI that enabled effective collaboration with experimentalists to select 2 promising candidates which we successfully synthesized and characterized.

To our knowledge, Yim et al. @yim_novel_2015 were the first to develop codes that fully automate ab-initio calculation of band gaps and dielectric permittivities. They calculated 1800 structures of binary and ternary oxides from the ICSD to generate a dielectric property map which confirmed the inverse correlation between band gap and permittivity for most oxides, with occasional outliers that exhibit both large permittivity despite large band gaps.

#cite(<petousis_benchmarking_2016>, form: "prose") @petousis_benchmarking_2016 calculated electronic and ionic dielectric tensors for 88 compounds to test the predictive power of DFPT against experiment for total dielectric constant and refractive index. While they observed a Mean Average Deviation (MARD) of 16.2% when using PBE as compared to LDA, they noted that DFPT is less accurate for compounds with complex structural effects or strong anharmonicity. Their results, however, showed a high Spearman correlation factor of 0.92, demonstrating the utility of DFPT in identifying promising materials by ranking.

The following year, #cite(<petousis_benchmarking_2016>, form: "prose") extended their previous work by running high-throughput DFPT on 1,056 inorganic compounds. The resulting database of dielectric tensors was integrated into the Materials Project for public access. While this greatly improved explorability of the data and likely may have helped expand the search pool for experimentalists seeking synthesis candidates, the scale of the data remained too limited to cover more than a small fraction of compositional and even less of the configurational space of potential high dielectrics.

While the above works resulted in novel and promising candidate materials, they relied exclusively on expensive DFPT calculations, making truly high-throughput screening of hundreds of thousands of materials cost-prohibitive. Yet they produced a sizeable pool of DFT dielectric properties with which we are now able to train ML models to accelerate and amortize the high cost of DFPT in the search for dielectrics, allowing screening of a much more expansive chemical space.

= Synthesis Development and Structure Fitting
<sec:Bi2Zr2O7-synthesis-development>

#BZO is known and has seen research interest for its use as a photocatalyst @wu_preparation_2015 @jayaraman_bridging_2020 @luo_new_2018. In these reports, the compound has been said to have either a stoichiometric pyrochlore structure (#ce("A2B2O7")) @pandey_metastable_2018 @luo_new_2018 @liu_bi2zr2o7_2018 @luo_synthesis_2019 @jayaraman_bridging_2020 @kurlla_greenengineered_2023 or the structurally related defect-fluorite structure @sorokina_new_1998 @sharma_synthesis_2013 @wu_preparation_2015 @rajashekharaiah_nuv_2019 @feng_unraveling_2021. Our results show that a pyrochlore could not be isolated without additional #ce("Bi2O3") or #ce("ZrO2") impurities due to the metastable nature of this compound. Though the pyrochlore and fluorite structures yield similar XRD patterns, with the most intense peaks located in the same positions, the absence of the (111) peak at $Q = #si4[1.01Å]$ favors assignment of the fluorite structure, @fig:exp-rietveld-Bi2Zr2O7-Fm3m.

The XRD data was fit using Rietveld refinement. Attempts were made to fit the data with a pyrochlore structure. When using both a standard pyrochlore model and models with oxygen and #ce("Bi^3+"), displacive disorder produces calculated patterns that fail to fit the data properly. Intensity mismatch is observed for low-angle pyrochlore peaks, specifically the (111) reflection. No amount of disorder was sufficient to reduce the intensity of this peak in the model to noise levels in the data, further confirming that this compound does not crystallize as a pyrochlore.

Using a defect-fluorite structure (#ce("Bi_0.5Zr_0.5O_1.75"), @fig:Bi2Zr2O7-whole-cell results in rapid model-to-data convergence with a good visual fit, @fig:exp-rietveld-Bi2Zr2O7-Fm3m. The resultant model shows atomic displacement parameters of $3.28(17) thin Å^2$ for the cations and $8.4(4) thin Å^2$ for the oxygen, which are large. Large atomic displacement parameters are commonly found in disordered compounds, and experimentally observable in the form of broad diffraction peaks, compared to @fig:exp-rietveld-CsTaTeO6-Fd3m. Attempts to account for the disorder in this compound in our structural model were not successful. Splitting the position of Zr and Bi to account for chemical displacements off their position in the center of the cubic polyhedra resulted in the cations refining back to their undisplaced positions. The same process was used for the oxygen positions but resulted in much larger atomic displacement parameters, leading us to discount this distortion. The occupancies of sites were also refined, resulting in the cations maintaining a 1:1 ratio, within error. This allowed us to conclude that a simple defect-fluorite structure is the most sensible model. This final model can be seen in @fig:Bi2Zr2O7-whole-cell and an isolated #ce("Zr/BiO8") polyhedra can be seen in @fig:Bi2Zr2O7-polyhedra. This model produced sensible metal-oxygen bond lengths of 2.3160(5)$thin$Å, which were expectedly longer than #ce("ZrO2") bond lengths of #si4[2.25Å].

= Synthesis Development and Structure Fitting
<sec:CsTaTeO6-synthesis-development>

The targeted #CTTO pyrochlore compound was initially investigated as it both met the figure of merit criterion and had not been reported previously in the ICSD or MP. However, we did find mention of this compound and its crystallographic analysis in @simon_synthesis_2010 after completing synthesis and characterization. Moreover, a related defect-pyrochlore with composition #ce("CsNbTeO6") had been reported in @fukina_structure_2021 @weiss_photoinduced_2020 from which we extracted initial synthesis parameters. With minor modifications of the synthetic procedure, the new compound was isolated in high purity, with only a 4.20 wt% #ce("Ta2O5") impurity.

@fig:exp-rietveld-CsTaTeO6-Fd3m shows XRD data of the final #CTTO product. This pattern indexes readily to the symmetry and lattice parameters of a cubic defect-pyrochlore (@fig:CsTaTeO6-whole-cell), consistent with both the #ce("Nb^5+")-based analog and the computational predictions. Rietveld refinements were initiated using parameters taken from Pawley fitting and readily converged to a defect-pyrochlore structural model. The structural model was taken from the refinement of #ce("CsNbTeO6") which places #ce("Cs") on the larger site 8b (@fig:CsTaTeO6-a-site) site and the #ce("Ta^5+") and #ce("Te^6+") in equimolar amounts on the 16c site (@fig:CsTaTeO6-b-site). This formulation is that of a defect-pyrochlore (#ce("AB2X6")), which is distinct from the traditional #ce("A2B2X6Y") pyrochlore structure. Relative to a traditional pyrochlore, this structure has both cation and anion vacancies, while maintaining the same anion packing and #ce("BO6") connectivity. After refining all parameters simultaneously, a good visual fit to the data is obtained with sensible atomic positions, sensible atomic displacement parameters $0.087(15) -- 0.78(2) thin Å^2$, a lattice parameter (10.29894(5)$thin$Å) close to that of the #ce("Nb^5+") analog (10.288)$thin$Å), and a fit quality parameter (Rwp = 8.095%) approaching that of the minimum set by the Pawley Fit (Rwp = 7.399%) @galati_cation_2008.

Due to the defect nature of this pyrochlore formulation, the #ce("Cs+") (A-site) adopts an octahedral polyhedral environment (@fig:CsTaTeO6-a-site) with six equal bond lengths of 3.183(6) #ce("Å"), instead of the cubic (AO8) environment found in stoichiometric #ce("A2B2O7") pyrochlores. The observed bond lengths are consistent with #ce("AO6") polyhedral environments seen in other #ce("Cs+") pyrochlores such as #ce("CsNbTeO6") or #ce("CsMoTeO6") which range from 3.180 -- 3.421 #ce("Å") @galati_cation_2008 @fukina_crystal_2019. The #ce("Ta^5+") and #ce("Te6+") occupy the smaller octahedral environment (@fig:CsTaTeO6-b-site) found in traditional and defect-pyrochlores. This environment generates bond lengths of 1.9430(18) #ce("Å"), again falling within the expected range of related materials such as the #ce("Nb^5+") and #ce("Mo^5+") analogs previously mentioned, compounds that range from 1.941 -- #si4[2.013Å]. This consistency of the structural environments found in #CTTO with similar chemistries further validates the quality of our model.

= Tradeoffs in Dielectric Materials for Computing Applications
<tradeoffs-in-dielectric-materials-for-computing-applications>
As indicated by the shaded regions in @fig:diel-total-vs-bandgap-mp, while ideal dielectric materials all push into the top right of this plot, different applications have different requirements. Materials for flash storage require especially large band gaps to minimize leakage current and maintain polarization over extended periods. CPU gate dielectrics trade off lower band gaps in exchange for increased permittivity which lowers the gate voltage required to achieve polarization and hence decreases power consumption. For random access memory (RAM) applications, increased leakage current resulting from a lower band gap is acceptable since RAM is memory-refreshed hundreds of times a second (stored data is read and immediately rewritten unmodified to preserve integrity to avoid polarization sapping over time). Instead, optimal RAM performance relies on exceptionally high permittivity so that each repolarization costs minimal energy. Our goal is to discover materials in any of these regions beyond the green isoline ($Phi_"M" = 240$). @fig:diel-parts-vs-bandgap-mp shows that the principal contributions to the permittivity are due to the ionic permittivity of the materials rather than their electronic permittivity.

#figure(
  pdf-img("figs/diel-total-vs-bandgap-mp.pdf", width: 300pt),
  caption: [
    2d histogram showing the $1 \/ x$ relationship between band gap and dielectric constant for 7.2k MP materials. The dashed isolines represent levels of constant figure of merit ($epsilon_"tot" dot E_"gap"$). The colored ellipses highlight the optimal trade-offs between band gap and permittivity for specific device applications. See @fig:diel-parts-vs-bandgap-mp for the same plot split by electronic and ionic contributions to the permittivity.
  ],
)<fig:diel-total-vs-bandgap-mp>

#figure(
  pdf-img("figs/diel-parts-vs-bandgap-mp.pdf"),
  caption: [
    Ionic (left) and electronic (right) parts of the dielectric constant. Ionic permittivity makes a much larger contribution than the total compared to electronic permittivity and is also much more likely to break the 1/x relationship with band gap.
  ],
)<fig:diel-parts-vs-bandgap-mp>

= DFPT Validation
<sec:dfpt-validation>
To validate our DFPT results, @fig:exp-vs-us-vs-petousis-diel-total compares our ab-initio results generated using the `wf_dielectric_constant` workflow in `atomate` @mathew_atomate_2017 against available experimental dielectric constants collected in @petousis_benchmarking_2016@petousis_high-throughput_2017. While we achieve better agreement with experiment than Petousis as indicated by the lower MAE of 16.5 (vs 20.4) and higher $R^2$ of 0.41 (vs 0.0), and similar performance to MP (MAE = 14.9, $R^2 = 0.12$), we incur a slightly larger fraction of outliers than either of them at 14% (vs 9% and 10%, respectively). We define outliers as points with absolute relative deviation greater than $plus.minus 50 %$ relative to experiment. The reason we nonetheless achieve higher $R^2$ is due to the lack of extreme outliers; we have more but they are less severe. This is advantageous in high-throughput settings where the goal is to guide experiment. Even rare cases of extreme outliers will show up given sufficient throughput and extreme permittivity overpredictions are more likely to result in wasted experimental effort.

We note that while the data in MP was generated with the same `atomate` workflow as designed and benchmarked by #cite(<petousis_benchmarking_2016>, form: "prose"), our data is expected to deviate from MP/Petousis due to our departure in choice of VASP parameters described in @sec:dfpt-to-dielectric, most notably the use of `PBE_54` POTCARs, increased $k$-point density of 3000 points per atom, increased `ENCUT` = 700~eV plane wave energy cutoff and decreased `EDIFF`$ = 10^−7 thin "eV"$ SCF convergence criterion. All of the above, though most notably the newer pseudopotentials may explain the less extreme outliers with respect to experiment. Overall, the variations with respect to MP/Petousis are within reason for run-to-run variability using slightly modified settings.

#figure(
  pdf-img("figs/exp-vs-us-vs-petousis-vs-mp-diel-total.pdf"),
  caption: [
    Comparison of experimental and DFPT-computed values for total permittivity $epsilon_"tot"$. Our data shows lower MAE and higher $R^2$ but more outliers (defined as points with $> 50 %$ error) compared to Petousis et al. Comparing our DFPT dielectric constants with experimental values, we achieve an MAE of 16.5 and $R^2$ of 0.4 while MP results attain a slightly lower MAE of 14.9 and $R^2$ of 0.125. A CSV file with the plotted experimental data is available on #link("https://github.com/janosh/dielectrics/blob/68839f9d8/data/others/petousis/exp-petousis.csv")[GitHub].
  ],
)<fig:exp-vs-us-vs-petousis-diel-total>

= Exploratory Data Analysis
<sec:exploratory-data-analysis>
#figure(
  pad(
    x: -3em,
    grid(
      columns: (1fr, 1fr),
      row-gutter: 9pt,
      column-gutter: 9pt,
      subfigure(
        pdf-img("figs/ptable-elem-counts-us.pdf"),
        caption: [
          Element occurrences
        ],
        label: <fig:ptable-elem-counts-us>,
      ),
      subfigure(
        pdf-img("figs/ptable-per-elem-fom-pbe.pdf"),
        caption: [
          $Phi_"M" = epsilon_"tot" dot E_"gap"$
        ],
        label: <fig:ptable-per-elem-fom-pbe>,
      ),

      subfigure(
        pdf-img("figs/ptable-per-elem-diel-ionic-pbe.pdf"),
        caption: [
          Ionic permittivity $epsilon_0$
        ],
        label: <fig:ptable-per-elem-diel-ionic-pbe>,
      ),
      subfigure(
        pdf-img("figs/ptable-per-elem-diel-elec-pbe.pdf"),
        caption: [
          Electronic permittivity $epsilon_oo$
        ],
        label: <fig:ptable-per-elem-diel-elec-pbe>,
      ),
    ),
  ),
  caption: [
    @fig:ptable-elem-counts-us Element occurrence counts, i.e. the number of structures among 2532 DFPT results containing a given element. @fig:ptable-per-elem-fom-pbe Figure of merit $Phi_"M" = epsilon_"tot" dot E_"gap"$ projected onto elements by composition and averaged over all 2532 structures. E.g. a #ce("Fe2O3") with a $Phi_"M"$ of 100 would contribute a sample of 40 to the mean heatmap value of #ce("Fe") and 60 to #ce("O"). @fig:ptable-per-elem-diel-ionic-pbe same as @fig:ptable-per-elem-fom-pbe but for ionic permittivity $epsilon_0$. @fig:ptable-per-elem-diel-elec-pbe same as @fig:ptable-per-elem-fom-pbe but for electronic permittivity $epsilon_oo$. We filtered out 10 untrustworthy calculations with electronic permittivity $epsilon_oo > 100$.
  ],
)<fig:ptable-per-elem>

@fig:ptable-per-elem shows the distribution of elements in our DFPT dataset (@fig:ptable-elem-counts-us) and their element-projected figure of merit $Phi_"M"$ (@fig:ptable-per-elem-fom-pbe) and electronic (@fig:ptable-per-elem-diel-elec-pbe) and ionic (@fig:ptable-per-elem-diel-ionic-pbe) permittivities $epsilon_oo$ and $epsilon_0$. The most prevalent elements in our dataset are #ce("Ta") (514), #ce("Pb") (329), #ce("Bi") (319), #ce("Ba") (319), #ce("Nb") (259) where the number in parentheses is the number of structures containing that element. Our data recovers well-known trends for elements that tend to be present in high dielectrics. In particular, @fig:ptable-per-elem-diel-ionic-pbe shows titanium has the highest ionic permittivity when averaged over all #ce("Ti")-containing structures in our dataset. This matches the prevalence of high dielectric alkaline earth metal titanates such as the perovskites #ce("BaTiO3") and #ce("SrTiO3"). @fig:ptable-per-elem-diel-elec-pbe reveals that late transition metals like #ce("Ru"), #ce("Rh"), #ce("Os"), #ce("Ir") and #ce("Pt") tend to yield the highest observed electronic permittivities.

@tab:table-fom-pbe-gt-350 lists all DFPT results in our dataset with $Phi_"M" > 350$ sorted by $Phi_"M"$. The highest-$Phi_"M"$ materials are almost exclusively oxides with only two fluorides and one selenide in the mix (#ce("AcF3"), #ce("LiY2F7") and #ce("Sm2CdSe4")). Some of the top materials, unfortunately, contain toxic or rare elements (e.g. #ce("Cd"), #ce("Nd"), #ce("Dy")) which are undesirable for environmental, economic and lab-safety/logistic reasons. Others contain lanthanides and actinides, f-block elements which DFT is known to struggle with due to strong electron correlation effects in the atomic-like $4 f$ orbitals near the valence band @soderlind_groundstate_2014. Both are strong arguments against attempting experimental synthesis, explaining why we did not simply select the top materials in this list.

#figure(
  pdf-img("figs/table-fom-pbe-gt-350.pdf"),
  caption: [
    Table of DFPT results with $Phi_"M" > 350$ sorted by $Phi_"M"$.
  ],
  kind: table,
)<tab:table-fom-pbe-gt-350>

= Band Gap Prediction
<sec:band-gap-model>
#figure(
  grid(
    columns: (1fr, 1fr),
    column-gutter: 9pt,
    row-gutter: 3pt,
    subfigure(
      pdf-img("figs/rolling-bandgap+diel-error-pbe-as-x.pdf"),
      caption: [
        RAE as a function of PBE band gap
      ],
      label: <fig:rolling-bandgap-diel-error-pbe-as-x>,
    ),
    subfigure(
      pdf-img("figs/rolling-bandgap+diel-error-wren-as-x.pdf"),
      caption: [
        RAE as a function of Wren band gap
      ],
      label: <fig:rolling-bandgap-diel-error-wren-as-x>,
    ),
  ),
  gap: 14pt,
  caption: [
    Rolling absolute error (RAE) of Wren band gap and dielectric constant predictions relative to DFPT.
  ],
)<fig:rolling-bandgap-diel-error>

In this screening campaign, we emphasize that substantial challenges remain concerning band gap prediction, due in part to a metal-heavy dataset imbalance and in part to band gaps being an inherently non-local property of the electronic rather than ionic structure. This makes the prediction problem poorly, if not ill-defined for a coarse-grained structural model with no concept of electronic degrees of freedom. We describe some attempts to mitigate this issue that achieved limited success but ultimately consider ML band gap prediction a high-impact but unsolved problem (see discussion @sec:discussion).

Our ensemble of 10 Wren band gap models trained with L1 loss achieved a deceivingly low $"MAE" = #si4[0.151eV]$ and high coefficient of determination $R^2 = 0.969$. This is largely due to the aforementioned dataset imbalance. 243095 / 319601 = 76.1% of the combined MP + WBM dataset are PBE metals. Not wanting to discard 3/4 of our training data, we attempted naive equal loss weighting across all samples as well as increased loss weighting of non-metals. Finally, we tried prepending a metal-nonmetal classifier to our band gap regressor to only predict the band gap for materials classified as non-metals. While the latter slightly decreased the false-positive rate, neither managed to significantly improve the overall performance of our band gap model nor fix this main failure mode in our discovery pipeline of metals classified as insulators/semiconductors. Many of the generated elemental substitution structures we predicted to have sizable band gaps turned out to be PBE metals. More recent efforts in training foundation models on giant datasets and then fine-tuning on smaller cognate datasets @shoghi_molecules_2023 have achieved impressive sub-#si4[100meV] band gap MAEs and may be able to overcome this issue.

@fig:rolling-bandgap-diel-error plots the rolling absolute error of our Wren band gap and dielectric constant ensembles with respect to DFPT using a variable window size of 300 samples. In @fig:rolling-bandgap-diel-error-pbe-as-x;, the bottom x-axis spans the range of PBE-computed band gaps for which we also have Wren predictions. Similarly, the top x-axis spans the range of DFPT-computed dielectric constants for which we also have Wren predictions. In @fig:rolling-bandgap-diel-error-wren-as-x;, we swap the x-axis values to be PBE instead. That is Wren band gap predictions on the bottom x-axis and Wren dielectric constants on the top x-axis. The y-axis is identical in both subplots: the rolling Wren-vs-DFPT absolute error for band gaps on the left and dielectric constants on the right.

@fig:rolling-bandgap-diel-error-pbe-as-x reveals that the error in dielectric constant shows a pronounced dip at intermediate ranges from about 40 to 120. This supports our initial argument for choosing dielectrics as the target material class for this discovery campaign. We hypothesized that by screening for materials near the pareto front when considering the trade-off between two opposing material properties, we can operate both the dielectric and band gap models in regions of good training support where ML models are most reliable and still discover materials with high $Phi_"M"$. In the case of the band gap model, this argument is less supported by the data. While the error in band gap prediction indeed drops significantly in our target region of $E_"gap" > #si4[2eV]$, the error does not increase again for extreme values but stays low even for outlier points beyond #si4[5eV]. However, small errors on large band gaps do not negatively affect the chances of dielectric materials discovery and so are not in conflict with our objective. The issue with the band gap model is that its error for small band gaps is $> #si4[2eV]$ and therefore large enough to predict metals as insulators, thereby introducing false positives into our discovery pipeline.

@fig:rolling-bandgap-diel-error-wren-as-x reveals that our workflow suffered from a negative feedback loop in that we purposely selected materials with large band gaps according to Wren which drew the bulk of our selection towards the lower end of the blue line. This line ends at a minimum band gap of #si4[2eV], indicating that no smaller Wren band gaps made it into our DFPT validation set. However, this is precisely the region where model error and its prediction are almost equal, resulting in a large number of false positive insulator predictions that turned out to be PBE metals.

#bibliography("references.bib")
