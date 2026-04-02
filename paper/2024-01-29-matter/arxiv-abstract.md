# Title: Pushing the Pareto Front of Band Gap and Permittivity: ML Guided Search for Dielectric Materials

Authors: Janosh Riebesell, T. Wesley Surta, Rhys Goodall, Michael W Gaultois, Alpha A Lee
Comments: 27 pages, 11 figures, 5 authors
Keywords: dielectrics, machine learning, high-throughput, materials discovery, multi-objective optimization, permittivity, functional materials

Author Emails:

- Janosh Riebesell: <janosh.riebesell@gmail.com>
- T. Wesley Surta: <wesley.surta@gmail.com>
- Rhys Goodall: <rhys.goodall@outlook.com>
- Michael W Gaultois: <m.gaultois@liverpool.ac.uk>
- Alpha A Lee: <aal44@cam.ac.uk>

Materials with high-dielectric constant easily polarize under external electric fields, allowing them to perform essential functions in many modern electronic devices.
Their practical utility is determined by two conflicting properties: high dielectric constants tend to occur in materials with narrow band gaps, limiting the operating voltage before dielectric breakdown.
We present a high-throughput workflow that combines element substitution, ML pre-screening, ab initio simulation and human expert intuition to efficiently explore the vast space of unknown materials for potential dielectrics, leading to the synthesis and characterization of two novel dielectric materials, CsTaTeO6 and Bi2Zr2O7.
Our key idea is to deploy ML in a multi-objective optimization setting with a concave Pareto front.
While usually considered more challenging than single-objective optimization, we argue and show preliminary evidence that the $1/x$-correlation between band gap and permittivity makes the task more amenable to ML methods by allowing separate models for band gap and permittivity to each operate in regions of good training support while still predicting materials of exceptional merit.
To our knowledge, this is the first instance of successful ML-guided multi-objective materials optimization achieving experimental synthesis and characterization.
CsTaTeO6 is a structure generated via element substitution not present in our reference data sources, thus exemplifying successful de-novo materials design.
Meanwhile, we report the first high-purity synthesis and dielectric characterization of Bi2Zr2O7 with a band gap of 2.27 eV and a permittivity of 20.5, meeting all target metrics of our multi-objective search.
