# Quantum Mathematics & Physics

[T]{.dropcap}he foundational mathematics of [quantum mechanics]{.index entry="Physics!Quantum Mechanics"} combines linear algebra, functional analysis, and probability theory. In this chapter, we illustrate LibroMorph's mathematical rendering pipeline in both EPUB (via native [MathML]{.index entry="Mathematics!MathML"}) and the web reader (via [MathJax 3]{.index entry="Mathematics!MathJax"}).

## Fundamental Postulates

In quantum theory, the physical state of an isolated system is represented by a unit vector $|\psi\rangle$ residing in a complex [Hilbert space]{.index entry="Mathematics!Hilbert Space"} $\mathcal{H}$.

The time-evolution of a non-relativistic quantum state is governed by the famous [Schrödinger equation]{.index entry="Schrödinger, Erwin!Equation"}:

$$i\hbar \frac{\partial}{\partial t} |\psi(t)\rangle = \hat{H} |\psi(t)\rangle$$

where $\hbar = \frac{h}{2\pi}$ represents the reduced [Planck constant]{.index entry="Planck, Max!Planck Constant"}, and $\hat{H}$ is the [Hamiltonian operator]{.index entry="Physics!Hamiltonian"} corresponding to the total energy of the physical system.

::: theorem
**Heisenberg's Uncertainty Principle**: Let $\hat{A}$ and $\hat{B}$ be two self-adjoint linear operators on a Hilbert space, with commutator $[\hat{A}, \hat{B}] = \hat{A}\hat{B} - \hat{B}\hat{A}$. The product of their standard deviations satisfies the lower bound:

$$\sigma_A \sigma_B \ge \frac{1}{2} \left| \langle [\hat{A}, \hat{B}] \rangle \right|$$

For position $\hat{x}$ and momentum $\hat{p}$, where $[\hat{x}, \hat{p}] = i\hbar$, this yields the iconic relation:

$$\Delta x \, \Delta p \ge \frac{\hbar}{2}$$
:::

## Special Relativity and Mass-Energy Equivalence

In his revolutionary 1905 paper on electrodynamics, [Albert Einstein]{.index entry="Einstein, Albert"} established the equivalence of inertial mass and energy:

$$E = mc^2$$

When generalized to relativistic four-momentum, the relation becomes:

$$E^2 = (pc)^2 + (m_0 c^2)^2$$

## Gaussian Integrals & Normalization

In wave mechanics, the normalization of a one-dimensional Gaussian wave packet involves the classical [Gaussian integral]{.index entry="Mathematics!Gaussian Integral"}:

$$\int_{-\infty}^{+\infty} e^{-a x^2} \, dx = \sqrt{\frac{\pi}{a}} \quad (a > 0)$$

For multi-dimensional integrations with a positive-definite symmetric matrix $\mathbf{A} \in \mathbb{R}^{n \times n}$:

$$\int_{\mathbb{R}^n} \exp\left(-\frac{1}{2} \mathbf{x}^T \mathbf{A} \mathbf{x} + \mathbf{J}^T \mathbf{x}\right) d^n\mathbf{x} = \sqrt{\frac{(2\pi)^n}{\det \mathbf{A}}} \exp\left(\frac{1}{2} \mathbf{J}^T \mathbf{A}^{-1} \mathbf{J}\right)$$

::: tip
In the HTML reader, mathematical formulas are fully interactive: you can right-click any equation to view MathML source, copy TeX markup, or activate equation zooming.
:::

## Concept Check: Quantum Fundamentals

Test your grasp of the principles introduced in this chapter:

::: quiz
**Question 1:** Which physical quantity represents the minimum non-zero commutator between position $\hat{x}$ and momentum $\hat{p}$?

- [ ] $c$ (Speed of light in vacuum)
- [x] $i\hbar$ (Imaginary unit times reduced Planck constant)
- [ ] $G$ (Newtonian gravitational constant)
- [ ] $k_B$ (Boltzmann constant)

*Explanation:* In canonical quantization, $[\hat{x}, \hat{p}] = i\hbar \hat{I}$. This fundamental non-commutativity is the mathematical origin of quantum uncertainty.
:::
