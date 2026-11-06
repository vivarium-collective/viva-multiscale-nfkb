# Bibliography

- Blinov ML, Faeder JR, Goldstein B, Hlavacek WS (2004). BioNetGen: software for rule-based modeling of signal
  transduction based on the interactions of molecular domains. *Bioinformatics* 20:3289–3291.
- Calzone L, Tournier L, Fourquet S, Thieffry D, Zhivotovsky B, Barillot E, Zinovyev A (2010). Mathematical modelling of
  cell-fate decision in response to death receptor engagement. *PLoS Comput Biol* 6(3):e1000702.
- Choi K, Medley JK, König M, Stocking K, Smith L, Gu S, Sauro HM (2018). Tellurium: an extensible python-based
  modeling environment for systems and synthetic biology. *Biosystems* 171:74–79. doi:10.1016/j.biosystems.2018.07.006.
  (The kinetic layer's engine wrapper.)
- Gillespie DT (1977). Exact stochastic simulation of coupled chemical reactions. *J Phys Chem* 81(25):2340–2361.
  (The algorithm MaBoSS uses.)
- Goldstein B, Perelson AS (1984). Equilibrium theory for the clustering of bivalent cell surface receptors by
  trivalent ligands. Application to histamine release from basophils. *Biophys J* 45(6):1109–1123.
  doi:10.1016/S0006-3495(84)84259-9. (The equilibrium oracle for a future runtime receptor layer.)
- Hindmarsh AC, Brown PN, Grant KE, Lee SL, Serban R, Shumaker DE, Woodward CS (2005). SUNDIALS: suite of nonlinear
  and differential/algebraic equation solvers. *ACM Trans Math Softw* 31(3):363–396. doi:10.1145/1089014.1089020.
  (CVODE, the integrator libRoadRunner uses.)
- Hoffmann A, Levchenko A, Scott ML, Baltimore D (2002). The IκB–NF-κB signaling module: temporal control and
  selective gene activation. *Science* 298:1241–1245. (BIOMD0000000140, a runner-up for the kinetic core.)
- Hoops S, Sahle S, Gauges R, Lee C, Pahle J, Simus N, Singhal M, Xu L, Mendes P, Kummer U (2006). COPASI—a COmplex
  PAthway SImulator. *Bioinformatics* 22(24):3067–3074. doi:10.1093/bioinformatics/btl485. (The second engine in the
  kinetic checks.)
- Lee REC, Qasaimeh MA, Xia X, Juncker D, Gaudet S (2016). NF-κB signalling and cell fate decisions in response to a
  short pulse of tumour necrosis factor. *Sci Rep* 6:39519. doi:10.1038/srep39519. (HeLa cells needed IFNγ
  sensitisation to die from TNF.)
- Lipniacki T, Paszek P, Brasier AR, Luxon B, Kimmel M (2004). Mathematical model of NF-κB regulatory module. *J Theor
  Biol* 228:195–215. (BIOMD0000000786.)
- Lipniacki T, Puszynski K, Paszek P, Brasier AR, Kimmel M (2007). Single TNFα trimers mediating NF-κB activation:
  stochastic robustness of NF-κB signaling. *BMC Bioinformatics* 8:376. doi:10.1186/1471-2105-8-376. (The precedent for
  reading receptor activation as Lipniacki's TNF input.)
- McMillan D, Martinez-Fleites C, Porter J, et al. (2021). Structural insights into the disruption of TNF-TNFR1
  signalling by small molecules stabilising a distorted TNF. *Nat Commun* 12:582.
- McNemar Q (1947). Note on the sampling error of the difference between correlated proportions or percentages.
  *Psychometrika* 12(2):153–157. doi:10.1007/BF02295996. (The paired test in Study 0.)
- Micheau O, Tschopp J (2003). Induction of TNF receptor I-mediated apoptosis via two sequential signaling complexes.
  *Cell* 114(2):181–190. doi:10.1016/s0092-8674(03)00521-x. (With NF-κB active, the death complex carries FLIP(L) and
  the cell survives.)
- Noé F, Nüske F (2013). A variational approach to modeling slow processes in stochastic dynamical systems.
  *Multiscale Model Simul* 11:635–655. (The method planned for finding the full composite's slow modes from simulated
  trajectories, where no equations are available.)
- Schliemann M, Bullinger E, Borchers S, Allgöwer F, Findeisen R, Scheurich P (2011). Heterogeneity reduces sensitivity
  of cell death for TNF-stimuli. *BMC Syst Biol* 5:204. (BIOMD0000000407, a runner-up; multicellular heterogeneity.)
- Somogyi ET, Bouteiller JM, Glazier JA, König M, Medley JK, Swat MH, Sauro HM (2015). libRoadRunner: a high
  performance SBML simulation and analysis library. *Bioinformatics* 31(20):3315–3321. doi:10.1093/bioinformatics/btv363.
- Stoll G, Viara E, Barillot E, Calzone L (2012). Continuous time Boolean modeling for biological signaling: application
  of Gillespie algorithm. *BMC Syst Biol* 6:116. (MaBoSS.)
- Wu CY, Huang CK, Chung CY, Huang IP, Hwu Y, Yang CS, Lai YK, Lo LW, Chiang SY (2011). Probing the binding kinetics
  of proinflammatory cytokine-antibody interactions using dual color fluorescence cross correlation spectroscopy.
  *Analyst* 136(10):2111–2118. doi:10.1039/c0an00995d. (TNFα's diffusion coefficient, 100.06 ± 4.9 µm²/s, with a
  hydrodynamic diameter of 4.89 nm that agrees with light scattering on native TNFα.)
