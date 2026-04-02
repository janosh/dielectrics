CC: <yan.li@cell.com>

Dr. Janosh Riebesell
Lawrence Berkeley National Laboratory
2601 Benvenue Ave
Berkeley, CA 94708
UNITED STATES

Mar 05, 2024

MATTER-D-24-00247
"Pushing the Pareto Front of Band Gap and Permittivity: ML Guided Search for Dielectric Materials"

Dear Dr. Riebesell,

I am enclosing the comments that reviewers provided on your paper. Unfortunately, the recommendation is against publication in Matter. The reviewers have a number of comments and criticisms, which I hope you will find useful and constructive. It is a matter of general policy that we do not propose re-submission of manuscripts when the reviewers present extensive criticisms, and we therefore cannot offer to consider this paper further. I appreciate that this outcome will be disappointing, but I hope you will find the reviewers' comments helpful as you prepare the manuscript for submission elsewhere.

Although we cannot offer to publish your manuscript, I recommend that you transfer it - without needing to reformat - to Cell Reports Physical Science, our premium open access journal which publishes cutting edge and impactful work from across the physical sciences, and which is led by professional Cell Press editors. The editors at Cell Reports Physical Science have already agreed to a 50% reduction of the Article Processing Charges.

We appreciate the work that you and your colleagues put into this paper and that this outcome will be disappointing; however, I hope that you will feel free to submit other papers to Matter in the future when it seems appropriate, and that this decision will ultimately lead to timely publication of this paper elsewhere.

If you have any questions about Cell Reports Physical Science and its scope, you can contact the Editor in Chief, Luke Batchelor, directly at <lbatchelor@cell.com>. I strongly recommend that you transfer this work to Cell Reports Physical Science and feel this will likely lead to the quickest publication. Moreover, 80% of the papers that were endorsed by a Matter editor and transferred with reviewer reports were accepted during 2020. On average this took two weeks once the revised manuscript was submitted.  Please visit our Rights, Sharing and Embargoes page for information about Article Processing Charges at our open access journals.

If you are interested in transferring your manuscript for independent consideration, please click on the link below to automatically transfer your manuscript: Agree to Transfer

This link will bring you to a page where you can confirm the transfer, which will activate the process.

If you decide not to transfer this manuscript to Cell Reports Physical Science, please click here: Decline to Transfer

This will officially close out the manuscript in our system. Please note that if you do not accept or decline by Apr 06, 2024, the system will automatically decline the invitation on your behalf.

Yours sincerely,

Sandra Skjaervoe, Ph.D.
Scientific Editor, Matter

Reviewer Comments:

Reviewer #1: The manuscript presents work on a topic of considerable importance within the field. The initiative to provide open access to the accompanying software is highly commendable and reflects a positive step toward fostering transparency and collaboration in scientific research. However, despite the potential interest this work may hold for the readership of Matter, there are several key areas where the manuscript does not yet meet the journal's high standards for publication.
The manuscript falls short of providing adequate detail to allow a full understanding of the scale of the work and the assumptions underpinning it. For the work to reach its full potential and be considered for publication in Matter, it is imperative that the authors expand upon the methodology, theoretical framework, specific assumptions made during their analysis, analysis of data, etc (see blow).
The application of identical computational methods to both phonon stable and unstable systems raises significant questions (at least to best of my understanding the calculation include both types of materials), particularly concerning the impact on the ionic contribution to the dielectric constant. The manuscript would benefit from a more detailed examination of the implications of this methodological choice, including any limitations or potential biases introduced and how they might affect the overall conclusions drawn from the study. I personally have significant doubts about whether the results for phonon unstable systems from current work would be fully reliable.
The manuscript discusses the underestimation of band gaps. This issue is critical as it suggests that the dataset may not accurately reflect the level of theoretical rigor necessary for reliable and meaningful analysis. To elevate the manuscript to the standard required by Matter, a more sophisticated approach to correcting these inaccuracies or a comprehensive discussion on the selection of the current method is needed. The problem here lies in the fact that the underestimation of the band gap is directly known to affect the dielectric constant (for instance, in the common literature this effect is correct with different approaches as simple as sissor correction). these thus means than means that both calculations of ionic and electronic contribution to dielectric constant is not done with sufficient accuracy to make it state of art work.
Given the above concerns, I am unable to recommend the manuscript for publication in its current form. However, this should not detract from the fact that the work addresses a significant topic with potential interest to the field. For me personally, I feel that without improving the quality of the dataset to much higher standards, it is not possible to consider this work for publication in Matter. I do, however, see that the work can be published in a more specialized journal even with the current dataset, which likely has a lot of misleading results and potential computational problems. For more specialized journals, the authors are still encouraged to more specifically provide details on their datasets, reflect and comment on phonon instability, and likely label phonon unstable systems in some way in their online resources, and generally admit that many of the results are likely very strongly affected by the underestimation of band gap, resulting in significant deviation in electronic contribution to the dielectric constant.

Reviewer #2:

Multi-objective optimisation in a topical problem in materials science, so I was happy to receive and read this manuscript. Overall, it is an impressive study, especially consider the integrated experimental validation. I have no hesitation in recommending it for publication in Matter.

Suggestions:

- Ground truth
A general reader would benefit in knowing the reliability of the underlying data used to guide the search. In particular, the smaller band gaps from GGA will typically exaggerate the dielectric constants. In extreme cases, such as transition metal systems, there can also be false metallic solutions that will break the workflow? The limitations should be opening discussed to support future improvements. I recommend even just taking one example such as ZnO, and comparing calculated and reference experimental values for Eform and epsilon ionic/electronic would be helpful. It can be argued that although individual errors may be large, the trend guiding the search should be reasonable, but it is important to state.

- Novelty
There are several statements claims of novelty, which are usually not recommended or necessary. For example, "To our knowledge, this is the first instance of" could be replaced by "This is a demonstration of". The strength of the study is self evident.

- Other
Figure 6 is hard to read - except for knowing that a web app exists, the font sizes are too small to extract any information. A focus on the central panel could be more helpful.

Reviewer #3:

The authors use computational methods (first-principles calculations and machine learning models) to identify new candidate materials for dielectrics. Two candidates are synthesized and characterized, with one of them demonstrating significant potential for the stated application. Overall, I find the work to be interesting, and there are indeed compelling aspects to the workflow and the findings. However, I believe there are a few technical issues and a significant over-inflation of novelty that deem the manuscript not suitable for publication in its current form.

1. The authors claim that what they are doing is multi-objective optimization. Certainly, the authors consider multiple objectives, but the optimization component is lacking. Instead, this appears to be high-throughput screening rather than optimization. Optimization implies iteratively working towards an extreme value in some objective function. This work is simply screening materials trying to find the one(s) with the highest pre-defined figure of merit. The only places where this figure of merit enters is in the seed crystals for ionic substitutions and the selection of which screened candidates deserve further experimental work. Neither of these involve optimization. Hence, it is not correct to say that this "is the first instance of successful ML-guided multi-objective materials optimization".

2. A general issue with this work is that common approaches are exaggerated or inflated. For instance, "the last selection step is an expert committee to incorporate human intuition…". This is in no way atypical as every high-throughput screening effort that includes an experimental component could claim this. This has potential to be a sound paper that brings together several previously published tools in a cohesive fashion (and with success!). The authors should simply make clear what is new and what is not.

3. The abstract states that the inverse relationship between band gap and permittivity makes the task more amenable to ML. There is minimal discussion and no concrete evidence that this is the case.

4. How do the synthesized CsTaTeO6 and Bi2Zr2O7 phases compare to the structures that were calculated/identified during the screening? In the beginning of the Discussion, it's stated that Rietveld verifies that the target structures were realized, but given other comments, it's not clear that this is the case. If this is the case, what was the seed crystal (before substitutions) that spawned CsTaTeO6 and is this the observed structure? Similarly, it appears Bi2Zr2O7 came from Materials Project during the screening, but the observed polymorph is different from the previously reported one. So, which one was identified from screening? If the observed structures are not the ones that were prototyped, then the authors can only claim that their method led them to interesting compositions, rather than materials.

5. CsTaTeO6 appears to be a clear failure of the approach. "… renders it unusable as a dielectric material." How is this consistent with the statement in the abstract that "CsTaTeO6 … thus exemplifying successful de novo materials design." The material design problem was to discover new dielectrics, so these statements are in direct conflict. Lowering the bar slightly, it's stated that the synthesis of CsTaTeO6 is a demonstration of de novo synthesis on a challenging metastable phase. A couple things aren't clear: 1) the evidence that this material is metastable (eg how metastable and with what level of theory?) and 2) that its synthesis is challenging. The synthesis protocol presented seems like a standard one for targeting thermodynamically stable phases.

6. The statement that the successful synthesis of CsTaTeO6 "shows that ML-driven thermodynamic stability predictions are reliable enough to be incorporated into a complex multi-step workflow." is a serious over-generalization. I don't disagree with the notion that these ML-driven stability predictions are useful, but basing this off of a single observation is a bit careless. Further, connecting this notion to "requiring sufficient trust" does not seem like a scientific conclusion. Solid-state chemists try to synthesize new materials regularly. The fact that a synthesis was attempted is not indicative of the reliability of the method.

7. Are the authors sure that CsTaTeO6 is pyrochlore? It seems odd to refer to this compound as the "simplest pyrochlore" given that the traditional pyrochlore has an A2B2X6Y prototype formula.

8. I don't follow the comparison of band gaps in 2.3.2. The authors state that the measured gaps are lower than the PBE band gaps, then note that a more accurate ML band gap model would have helped. The first comparison is experiment vs PBE. What does that have to do with the ML model? Subsequently, it's stated that training the ML band gap model on higher level DFT would have helped. I don't follow this logic. The PBE band gap is higher than the measured band gap. This suggests that the structure used in the DFT calculation is not the structure made experimentally. This mismatch has nothing to do with the level of theory or the band gap model. More information is needed to understand whether the screening approach identified the material that was made. If it did not, then this warrants some discussion of limitations.

9. When discussing the band gap of Bi2Zr2O7 compared to previous reports, it's stated that the higher band gap measured here indicates reduced defect states, higher purity, and distinct phase of the synthesized material compared to the literature. The last point suggests that you've made a different polymorph than Ref 31. If that is the case, then comparing the band gaps does not tell you anything about defect concentration or purity.

Reviewer #4:

The manuscript by Riebesell et al. describe a ML-assisted search for dielectric materials. A funnel-like screening procedure is used to narrow down candidate materials by formation energy, band gap, and dielectric constant; this ended in ~2600 candidates which are validated by DFT. Of these, two candidates were eventually chosen to be experimentally synthesized, with one material being unsuitable and another being promising (Bi2Zr2O7). In general this is a reasonable ML/computational high-throughput screening attempt, though the connection to experiment and feasibility as a reliable method for discovering dielectrics is somewhat tenuous. Arguably it is difficult to conclude that this framework can identify experimentally verifiable dielectrics based on the results in this manuscript. From a methodology standpoint, the approaches used are from established techniques. There are a number of concerns, which are communicated below:

> The performance in predicting formation energy, gap, and dielectric constant is better understood with parity plots of predicted vs actual properties; it is recommended that these figures are included for the ML models
>
> Fundamentally, in trying to go beyond the pareto plot, ML models will by definition be in a out of distribution setting. Unless more rigorous investigation and validation of the ML model performance for out of distribution performance (OOD in terms of material/composition, as well as property values), one cannot rely on these results.
>
> In general there is a serious concern how effective a screening criterion for materials is, when using a ML model (which authors themselves note to have problem with band gap prediction, and perhaps for dielectric as well), on top of training on PBE gaps which are completely unreliable. The amount of both false positive and false negative will invariably be high; indeed for 1 out of 2 experimentally synthesized materials, the framework is off the mark. One would reasonably conclude from the current results that this method is still premature until a more accurate ML model and DFT dataset (perhaps with hybrid functional data) is used.
>
> As with the majority of high throughput screening studies which include an experimental component, the selection of the two experimental candidates is not particularly systematic/transparent. The authors do list some criterion near the end of the paper, however it would help to show how many candidates were initial investigated, and how many were removed from the list due to being in one or more of these criteria for discarding. As it stands, there is a large jump from ~2600 candidates down to two without a clear flow (and this selection arguably does more heavy lifting than the entire computational workflow itself). Conversely, if one cannot trust the figure of merit provided by the workflow directly, this would suggest that the workflow still needs significantly more work to be practically used by others.
>
> Authors describe a "generative" component to the workflow, which creates new materials out of distribution from the database by template substitution.Is there a measure of how successful this method is relative to screening from existing materials? What percentage of generated structures made it to the final cut of ~2600 materials, compared to what percentage of existing database materials?
>
> In Figure 3, authors should highlight where the two materials CsTaTeO6 and Bi2Zr2O7 lie in that plot.

# TODOs

You get phonon modes from DFPT calcs, and so you can filter for imaginary modes which we didn't do but makes perfect sense (I didn't know this back when running the calcs)

There's definitely a smart way to bring in MACE-MP with its 81% accuracy on dynamic stability classification here. But that could easily turn into another project entirely

for now: just need to address the language concerns, add some more discussion and resubmit to somewhere less competitive like Digital Discovery

contrast to reviewer 2 is somewhat indicative of how ML is viewed by many

The problem is we also know the ML isn't good
Which was the balance we tried to get right

The question about pbe being an overestimation implying a different structure seems worth looking into

Rhys was also surprised it was called a pyrochlore when the formula didn't seem to match [Needs another meeting with Wes]

Maybe the title should change also as I think r3 didn't get the hypothesis applied only to concave fronts
but they're right that 1/2 isn't conclusive proof
We suggested it worked rather than said it was inconclusive

light of the reviewer comments the bandgap issue may be due to the fact that both the structures are actually different from the DFT structures. In both cases we appear to have phases with oxygen vacancies, Wes seemingly didn't prefix these as defect-fluorite and defect-pyrochlore which was the source of confusion R3 had. So the things we made weren't actually the structures we wanted just the compositions. In light of that I think that the things to do would be: repeat the DFT on the defect-prototypes we actually observed and then compare the results of the expected and realized structures and then redraft a more discursive conclusion that talks about more about the limitations. These pyrochlore, defect pyrochlore and defect fluorite structures seem to be quite similar

Do we have the phonon/raw files to get the phonons for the materials we ran dft on? can we just add a phonon filter to the table retrospectively and hope the two materials pass?

if we wanted to go the extra mile, we could calculate HSE band gaps
