# Diffusion: the spatial oracles

The spatial layer solves $\partial_t c = D\nabla^2 c - kc$ for the TNF concentration $c(\mathbf x, t)$ in a
rectangular box with reflecting (zero-flux) walls. The scheme is finite-volume and backward-Euler implicit in diffusion.

## A Gaussian bolus

In free space in two dimensions, an initial Gaussian of width $\sigma_0$ stays Gaussian, with its width growing as

$$
c(r, t) = \frac{M}{2\pi\sigma(t)^2}\,e^{-r^2/2\sigma(t)^2},\qquad \sigma(t)^2 = \sigma_0^2 + 2Dt .
$$

In a box, reflecting walls add mirror-image Gaussians (the method of images). When the walls are more than about 2.5σ
away, as in `checks/spatial/gaussian-diffusion`, the image terms are negligible, and the free-space solution is the
oracle. That check uses $\sigma_0 = 10\ \mu\text{m}$, $D = 50\ \mu\text{m}^2/\text{s}$ and a 200 × 200 µm box, read at
the centre and at 20 and 40 µm.

A bolus is also study 1's moving front ({doc}`../design/studies`). A cell at distance $r$ sees the concentration rise,
peak and fall as the Gaussian widens past it.

## A uniform bath with decay

With no gradient, diffusion does nothing, and the field decays everywhere as $c(t) = c_0 e^{-kt}$. `uniform-bath-decay`
checks that the field stays uniform (centre, corners and an edge agree) and follows this, rel 1e-5.

## Mass

With zero-flux walls and $k = 0$, the total $\int c\,d\mathbf x$ is conserved. `RegionTotal` (U2) reports it over a
region, weighted by each node's control volume, as the scheme conserves it. U2's tests check conservation to rel 1e-12.

## Resolution

The scheme's error in a front's tail falls as dx and dt shrink: +1.15% at dx 2 µm / dt 0.01 s, +0.29% at dx 1 µm / dt
0.0025 s, at $r = 40\ \mu\text{m}$, $t = 1\ \text{s}$ ({doc}`../design/spatial`).
