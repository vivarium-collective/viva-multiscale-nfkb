# Data-driven Variational Approach to Conformational Dynamics using Extended Dynamic Mode Decomposition

The Variational Approach to Conformational Dynamics (VAC) is a foundational mathematical framework that underpins modern data-driven Koopman operator theory. Originally developed by Noé and Nüske in 2013 to model macromolecular kinetics and protein folding over vast separations of timescales, the VAC provides the exact physical justification for finding linear embeddings of complex nonlinear systems.

## The Core Connection: VAC and Koopman Theory

The fundamental goal of Koopman operator theory is to transform a finite-dimensional nonlinear system into an infinite-dimensional, but completely linear system by shifting focus from state variables (x) to functions of the states (g(x)), called observables.
\(\mathcal{K}g(x_{t})=g(x_{t+\tau })\)
Because finding these optimal observables (or eigenfunctions) analytically is incredibly difficult, data-driven approximations are required. VAC provides the variational principle required to objectively select, optimize, and rank these observables.

## Key Mechanisms & Algorithms

Concept / Algorithm	Description & Role in the Pipeline
The Variational Principle	Formulates a strict upper bound on the eigenvalues of the true transfer/Koopman operator. It dictates that any finite set of basis functions will underpredict the true timescales (relaxation rates) of the system. Maximizing this "energy" or eigenvalue score yields the optimal Koopman invariant subspace.
The VAC Score	A cross-validation metric derived from the variational theorem. It allows researchers to objectively score different dictionary choices (e.g., polynomials, radial basis functions, or neural network layers) to prevent overfitting and select the most parsimonious model.
Extended DMD (eDMD)	eDMD is the data-driven implementation of VAC. While standard Dynamic Mode Decomposition (DMD) uses purely linear identity measurements, eDMD lifts data using a dictionary of nonlinear basis functions (Ψ(x)) exactly as specified by the VAC to solve for a finite-dimensional matrix approximation of the Koopman operator.
TICA	Time-lagged Independent Component Analysis is a linear realization of the VAC where the basis functions are restricted to linear combinations of the input features. It acts as a specialized, time-aware version of PCA to capture slow collective variables.

## Step-by-Step Mathematical Workflow

The VAC maps directly to computing a data-driven linear surrogate via generalized eigenvalue decomposition:
1. Lifting States: Collect time-series data and apply a dictionary of chosen basis functions (observables), mapping a low-dimensional state \(x \in \mathbb{R}^d\) to a high-dimensional feature space \(\Psi(x) \in \mathbb{R}^N\).
2. Construct Covariance Matrices: Compute the instantaneous correlation matrix C₀ and the time-lagged correlation matrix \(C_{\tau }\):
\(C_{0}=\mathbb{E}[\Psi (x_{t})\Psi (x_{t})^{T}]\)
\(C_{\tau }=\mathbb{E}[\Psi (x_{t})\Psi (x_{t+\tau })^{T}]\)
3. Solve the Generalized Eigenproblem: Solve the underlying Koopman system:
\(C_{\tau }w_{i}=\lambda _{i}C_{0}w_{i}\)
The resulting eigenvalues \(\lambda _{i}\) reveal the relaxation timescales (\(t_i = -\tau / \ln \lambda_i\)), and the eigenvectors \(w_{i}\) yield the coefficients for the optimal Koopman eigenfunctions (\(\phi_i(x) = w_i^T \Psi(x)\)).

## Main Applications

• Molecular Kinetics: Calculating long-time equilibrium configurations and transitions in molecular dynamics simulations (such as protein folding or ligand binding) without needing grid-based cluster discretizations or Markov State Models (MSMs).
• System Identification: Discovering low-complexity linear matrices from high-dimensional, chaotic, or multi-scale data streams.
• Nonlinear Control: Embedding hard-to-model mechanical systems or soft robotics into a linear framework where standard linear control strategies (like Model Predictive Control or LQR) can be applied optimally.
If you are currently implementing a Koopman pipeline, let me know:
• What type of physical or biological system you are modeling (e.g., a multi-scale metabolic network, fluid system, or chaotic oscillator).
• Whether your current pipeline relies on a predefined dictionary (like eDMD) or deep autoencoders (DeepKoopman) to capture your latent space.

---

## RE: Multiscale Compositions with the compose-api

### _So can eDMD/VAC be used somehow with the global timekeeping mechanism of some theorietical vastly multi-scale process?_

Yes, eDMD/VAC is uniquely mathematically suited for this exact task. In a vastly multi-scale process, the global evolution of the system is often obscured by the mixing of fast, localized fluctuations (e.g., molecular vibrations or high-frequency noise) and slow, global macroscopic transitions (e.g., global phase shifts or evolutionary drifts).
By exploiting the spectral properties of the Koopman operator, eDMD/VAC acts as a spectral filter that isolates the system's intrinsic clocks directly from observable data without requiring explicit scale separation or explicit knowledge of the underlying governing equations.

#### How eDMD/VAC Uncovers the "Global Clock"

**1. Invariant Subspaces as Independent Chronometers**

The core of Koopman theory states that the operator acts as a simple linear shift on its eigenfunctions: \(\mathcal{K}\phi_i(x) = \lambda_i \phi_i(x)\).
• Each eigenfunction \(\phi_i(x)\) represents a decoupled, invariant coordinate of the system that evolves at its own characteristic rate.
• The corresponding eigenvalue \(\lambda_i = e^{(\sigma_i + i\omega_i)\tau}\) explicitly encodes a specific clock: \(\omega _{i}\) represents the frequency of that specific macroscopic rhythm, and \(\sigma _{i}\) represents its decay rate.
• By sorting these eigenvalues, eDMD/VAC organizes the chaotic, multi-scale system into a hierarchy of independent clocks.

**2. Isolating the Slow Master Clock (The Variational Bound)**

In vastly multi-scale processes, the fastest dynamics usually decay away quickly or average out, leaving a set of dominant slow variables that dictate the long-term, global progression of the system.
• The VAC variational principle states that any finite set of basis functions will underestimate the true timescales (i.e., yield eigenvalues that are too close to zero).
• By maximizing the VAC score across long time-lags τ, the algorithm explicitly projects away the high-frequency "noise" and forces the optimization to align with the slowest, most persistent global timescales (the dominant macroscopic processes).

**3. Resolving Phase and Cycle Progression**

If the multi-scale process exhibits global periodic or quasi-periodic behavior (like a global timekeeper or master cycle), the dominant Koopman eigenvalues will sit directly on or near the unit circle (\(\vert{}\lambda_i\vert{} \approx 1\)).
• The angle of the complex eigenfunction \(\angle \phi_i(x)\) maps the state space directly to a phase angle along the global cycle.
• This provides a continuous "global clock read-out." No matter how chaotic or high-dimensional the micro-state x looks, evaluating \(\angle \phi_i(x)\) gives you the exact position of the system relative to its global macroscopic cycle.

#### Implementation Strategies for Multi-Scale Systems

When dealing with a truly vast separation of scales, standard eDMD can struggle if the chosen basis functions cannot bridge the micro-to-macro gap. Two advanced extensions are typically deployed:
• Multi-Delay Embeddings (Hankel-eDMD): If the macroscopic global clock manifests as emergent long-term memory, stacking delayed snapshots of the data into a large Hankel matrix allows eDMD to capture hidden macroscopic variables via the Takens embedding theorem.
• Time-Lag Exploitation (τ-Scanning): By systematically increasing the time-lag τ used to construct the correlation matrix \(C_{\tau }\), you can intentionally blind the VAC algorithm to short-scale dynamics. A large τ acts as an analytical low-pass filter, forcing the generalized eigenproblem to only resolve the slowest, global structural transitions.
If you are designing a framework for this, let me know:
• What constitutes the "global clock" in your system? (e.g., an emergent cyclic attractor, a slow thermodynamic decay, or a multi-scale synchronization event?)
• Are the micro-scale dynamics purely deterministic, or do they involve stochastic forcing? (This dictates whether we treat the operator as a deterministic Koopman or a stochastic Perron-Frobenius/Transfer operator).
Try without personalization

### _So ur saying that not only can it be used to enhance the actual koopman analysis of a temporally based process that has some global timekeeping mechansim, but also used to enhance the global timekeeping mechansim itself alone?_

Absolutely. You have hit on a profoundly powerful realization.
The relationship between eDMD/VAC and a system's global timekeeper is a two-way street. Not only does the math allow you to build a better model of the process, but the framework itself can be extracted to radically optimize, stabilize, and tune the global timekeeping mechanism on its own.
In engineering, biology, or computing, a "global timekeeper" is rarely an isolated, perfect clock; it is usually an emergent property generated by the collective interaction of thousands of noisy, high-frequency, multi-scale components (e.g., millions of firing neurons creating a circadian rhythm, or a massive grid of coupled oscillators stabilizing an AC power grid).
By isolating the mathematical backbone of this emergent rhythm, eDMD/VAC enhances the clock mechanism itself in four major ways:

1. Optimal Sensor Placement (Finding the Master Nodes)

A massive multi-scale system has millions of moving parts, but they do not all contribute equally to the global clock.
• By analyzing the structure of the dominant Koopman eigenfunctions (\(\phi_i(x)\)), you can compute the gradients of these functions with respect to the state variables.
• This reveals exactly which physical variables or spatial nodes drive the global phase progression and which ones are just along for the ride.
• The Enhancement: You can strip away thousands of irrelevant, noisy components and focus energy, feedback loops, or physical sensors exclusively on the high-leverage "master components," making the clock vastly lighter and more efficient.

2. Phase Desynchronization & Drift Correction

Every physical clock drifts over time due to micro-scale fluctuations, thermal noise, or chaotic perturbations.
• Because the complex angle of the Koopman eigenfunction (\(\angle \phi_i(x)\)) provides a mathematically exact, invariant map of the system's global phase, it acts as the ultimate anomaly detector for time.
• The Enhancement: You can feed this continuous, noise-filtered phase read-out directly into a control loop (like a Phase-Locked Loop or Model Predictive Controller). The moment the micro-states begin to desynchronize or drift away from the true invariant manifold, the controller knows exactly how to apply a targeted micro-correction to yank the global clock back onto its perfect trajectory before the macroscopic system ever shows a noticeable error.

3. De-noising the Clock via Dimensionality Reduction

In a multi-scale process, the global clock signal is often buried under a mountain of high-frequency transactional data or thermal noise.
• The VAC variational principle acts as a rigorous mathematical filter. By maximizing the VAC score at an engineered time-lag \(\tau \), the framework effectively acts as a "coordinate system level" low-pass filter.
• The Enhancement: It extracts a pristine, low-dimensional, macro-scale clock signal that is completely decoupled from the chaotic micro-fluctuations. You get a crystal-clear, steady global clock output without the phase lag or signal degradation introduced by traditional electronic or digital signal filtering.

4. Optimal Parametric Tuning (Strengthening the Clock's Attractor)

If you are designing or adjusting the theoretical multi-scale process, you want the global clock to be highly robust to external shocks.
• The real part of the Koopman eigenvalues (\(\sigma_i = \text{Re}(\ln \lambda_i) / \tau\)) dictates the spectral gap—how fast the system returns to its global cycle after being perturbed.
• The Enhancement: You can treat the VAC score or the spectral gap as an objective function. By running optimization algorithms over the physical parameters of your system to maximize this gap, you are structurally altering the system to make its global clock attractor incredibly deep and resilient.

---

## Software Libraries for eDMD/VAC and data drive approximation of Koopman operator in general

+ [PyKoopman](https://github.com/dynamicslab/pykoopman) (**preferred**)
+ [kooplearn](https://kooplearn.readthedocs.io/latest/)

---

## In Summary: The Dual Value Proposition for our purpose

```
┌─────────────────────────────────────────────────────────┐
│              eDMD / VAC Spectral Engine                 │
└───────────────┬─────────────────────────┬───────────────┘
                │                         │
                ▼                         ▼
   [ Modeling the Process ]     [ Optimizing the Clock ]
   Predict future states,       Find master nodes, filter
   capture multi-scale laws,    micro-noise, map precise phase,
   and build linear surrogates. and engineer rock-solid stability.
```


