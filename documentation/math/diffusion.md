# Diffusion: the spatial oracles

The spatial layer solves the diffusion equation with first-order decay,

$$
\partial_t c = D\nabla^2 c - \lambda c ,
$$

for the TNF concentration $c(\mathbf x, t)$ on a two-dimensional grid in a rectangular box with reflecting (zero-flux)
walls. $D$ is the diffusion coefficient and $\lambda$ the decay rate (written $\lambda$ here so as not to clash with
`k_time`). Why two dimensions rather than three is not yet argued in these pages; every run here uses a 2D grid.

**How it is solved.** The scheme is **finite-volume**: the box is divided into small cells (control volumes), and each
step moves TNF between neighbouring cells in proportion to their concentration difference, so no TNF is created or
lost by the bookkeeping. Each step is **backward Euler** (implicit) in diffusion: the new concentrations are found by
solving the step's equations for the end of the step rather than extrapolating from its start, which stays stable
for any step size.

## A Gaussian bolus

Diffusion spreads each point of a field into a Gaussian whose variance along each axis grows as $2Dt$ (the heat
kernel). Spreading a Gaussian of variance $\sigma_0^2$ by another Gaussian adds the variances. So in free space in two
dimensions, an initial Gaussian of width $\sigma_0$ and total amount $M = \int c\,d\mathbf x$ stays Gaussian:

$$
c(r, t) = \frac{M}{2\pi\sigma(t)^2}\,e^{-r^2/2\sigma(t)^2},\qquad \sigma(t)^2 = \sigma_0^2 + 2Dt .
$$

In a box, a reflecting wall acts like a mirror: the solution is the free-space Gaussian plus a mirror-image Gaussian
on the far side of each wall (the method of images). An image at distance $d_\text{img}$ from a point, against the
real source at distance $d$, contributes a fraction $e^{-(d_\text{img}^2 - d^2)/2\sigma^2}$ of the direct term.

`checks/spatial/gaussian-diffusion` uses $\sigma_0 = 10\ \mu\text{m}$, $D = 50\ \mu\text{m}^2/\text{s}$ and a
200 × 200 µm box with the bolus at the centre, read at the centre and at 20 and 40 µm every second to 10 s. At 10 s,
$\sigma = \sqrt{100 + 1000} = 33\ \mu\text{m}$ and the walls are 100 µm, or $3.0\sigma$, away. At 40 µm toward a wall,
the nearest image is 160 µm away, so it adds $e^{-(160^2 - 40^2)/(2 \cdot 1100)} \approx 2\times10^{-5}$ of the direct
term, far below the check's 1% tolerance. So the free-space solution is the oracle.

A bolus is also study 1's moving front ({doc}`../design/studies`). A cell at distance $r$ sees the concentration rise,
peak and fall as the Gaussian widens past it.

## A uniform bath with decay

With no gradient, diffusion does nothing, and the field decays everywhere as $c(t) = c_0 e^{-\lambda t}$. `uniform-bath-decay`
checks that the field stays uniform (centre, corners and an edge agree) and follows this, to a relative tolerance of
$10^{-5}$ ("rel 1e-5" in the checks).

## Mass

With zero-flux walls and $\lambda = 0$, the total $\int c\,d\mathbf x$ is conserved. `RegionTotal` (being added upstream to
viva-pde-particle for this project, in review as viva-pde-particle#70) reports it over a region, weighting each grid point by its control volume, as the
scheme conserves it. Its tests check conservation to rel 1e-12.

## Resolution

The scheme's error in a front's tail falls as dx and dt shrink: +1.15% at dx 2 µm / dt 0.01 s, +0.29% at dx 1 µm / dt
0.0025 s, at $r = 40\ \mu\text{m}$, $t = 1\ \text{s}$ ({doc}`../design/spatial`).
