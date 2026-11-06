"""Write documentation/science/_lipniacki_{species,reactions}.md from the pinned Lipniacki 2004 SBML, and prove that
total NF-kB is conserved.

Everything is read from workspace/datasets/lipniacki2004/processed/lipniacki2004_driven.xml (BIOMD0000000786 with its
stimulus event removed; that dataset's README). Function definitions are expanded by libSBML's own converter, so each
rate law is shown as the model computes it. The conservation proof builds every species' rate of change from the
reactions with sympy, then checks that d/dt of the model's own NFKB_total rule is identically zero. The script stops if
it is not, or if MEANING does not name exactly the model's species. Only the meaning of each species is written by hand.

    uv run --project compose python -I documentation/science/code/lipniacki_model.py           # write the tables
    uv run --project compose python -I documentation/science/code/lipniacki_model.py --check   # fail if they are stale
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import NoReturn

import libsbml
import sympy

ROOT = Path(__file__).resolve().parents[3]
SBML = ROOT / "workspace" / "datasets" / "lipniacki2004" / "processed" / "lipniacki2004_driven.xml"
OUT = {"species": ROOT / "documentation" / "science" / "_lipniacki_species.md",
       "reactions": ROOT / "documentation" / "science" / "_lipniacki_reactions.md"}

MEANING = {
    "TNF": "TNF signal at the receptor, 0 to 1; set from the composite's `TNF_R` (a boundary species: no reaction changes it)",
    "IKK_neutral": "IKK, the IκB kinase, in its neutral (ready) form",
    "IKK_active": "IKK activated by TNF",
    "IKK_inact": "IKK inactivated, spontaneously or by A20",
    "IkB": "free IκBα, NF-κB's inhibitor",
    "IKKactive_IkB": "active IKK bound to free IκBα",
    "IkB_NFKB": "IκBα bound to NF-κB: the resting, inactive form of NF-κB",
    "IKKactive_IkB_NFKB": "active IKK bound to the IκBα–NF-κB complex",
    "NFKB": "free NF-κB",
    "NFKB_nuc": "free NF-κB in the nucleus: the active transcription factor",
    "IkB_nuc": "free IκBα in the nucleus",
    "IkB_NFKB_nuc": "IκBα–NF-κB complex in the nucleus, on its way out",
    "IkB_mRNA": "IκBα mRNA, made on NF-κB's orders",
    "A20_mRNA": "A20 mRNA, made on NF-κB's orders",
    "A20": "A20 protein, which inactivates IKK",
    "cgen_mRNA": "mRNA of a control gene, made on NF-κB's orders and read by nothing (a transcription reporter)",
}
NFKB_CARRIERS = ("IKKactive_IkB_NFKB", "NFKB", "IkB_NFKB", "NFKB_nuc", "IkB_NFKB_nuc")


def _fail(message: str) -> NoReturn:
    sys.exit(f"lipniacki_model.py: {message}")


def _document() -> libsbml.SBMLDocument:
    """The SBML with its function definitions expanded. Callers keep the document referenced while they use its
    model: libSBML frees a model together with its document."""
    document = libsbml.readSBMLFromFile(str(SBML))
    properties = libsbml.ConversionProperties()
    properties.addOption("expandFunctionDefinitions", True)
    if document.convert(properties) != libsbml.LIBSBML_OPERATION_SUCCESS:
        _fail("libSBML could not expand the function definitions")
    return document


def _symbols(model: libsbml.Model) -> dict[str, sympy.Symbol]:
    ids = [s.getId() for s in model.getListOfSpecies()] + [p.getId() for p in model.getListOfParameters()]
    ids += [c.getId() for c in model.getListOfCompartments()]
    return {i: sympy.Symbol(i) for i in ids}  # explicit symbols, so no id is read as a sympy built-in


def _expr(math: libsbml.ASTNode, symbols: dict[str, sympy.Symbol]) -> sympy.Expr:
    return sympy.parse_expr(libsbml.formulaToL3String(math), local_dict=symbols)


def prove_conservation(model: libsbml.Model) -> str:
    symbols = _symbols(model)
    unit = {symbols[c.getId()]: 1 for c in model.getListOfCompartments()}
    if any(c.getSize() != 1.0 for c in model.getListOfCompartments()):
        _fail("a compartment's size is not 1; the rates below assume it")
    rate = {s.getId(): sympy.Integer(0) for s in model.getListOfSpecies()}
    for r in model.getListOfReactions():
        flux = _expr(r.getKineticLaw().getMath(), symbols).subs(list(unit.items()))
        for x in r.getListOfReactants():
            rate[x.getSpecies()] -= x.getStoichiometry() * flux
        for x in r.getListOfProducts():
            rate[x.getSpecies()] += x.getStoichiometry() * flux
    rule = model.getAssignmentRuleByVariable("NFKB_total")
    if rule is None:
        _fail("the model has no NFKB_total rule")
    # The rule divides by ModelValue_1, which an initial assignment sets to Kv: apply every initial assignment so the
    # proof uses the same quantity the reactions do.
    assigned = {symbols[a.getSymbol()]: _expr(a.getMath(), symbols) for a in model.getListOfInitialAssignments()
                if a.getSymbol() in symbols}
    total = _expr(rule.getMath(), symbols).subs(list(assigned.items()))
    carried = {str(s) for s in total.free_symbols} & set(rate)
    if carried != set(NFKB_CARRIERS):
        _fail(f"NFKB_total sums {sorted(carried)}, expected {sorted(NFKB_CARRIERS)}")
    derivative = sympy.Add(*(sympy.diff(total, symbols[s]) * rate[s] for s in carried))
    if sympy.simplify(derivative) != 0:
        _fail(f"d(NFKB_total)/dt is not zero: {sympy.simplify(derivative)}")
    return libsbml.formulaToL3String(rule.getMath())


def _equation(r: libsbml.Reaction) -> str:
    left = " + ".join(x.getSpecies() for x in r.getListOfReactants()) or "∅"
    right = " + ".join(x.getSpecies() for x in r.getListOfProducts()) or "∅"
    modifiers = ", ".join(x.getSpecies() for x in r.getListOfModifiers())
    return f"{left} → {right}" + (f" (driven by {modifiers})" if modifiers else "")


def tables() -> dict[str, str]:
    document = _document()
    model = document.getModel()
    if model is None:
        _fail("the SBML has no model")
    species = [s.getId() for s in model.getListOfSpecies()]
    if set(species) != set(MEANING):
        _fail(f"MEANING does not name exactly the model's species: {sorted(set(species) ^ set(MEANING))}")
    rule = prove_conservation(model)
    header = "<!-- Generated by documentation/science/code/lipniacki_model.py from the pinned SBML; do not edit. -->\n"
    rows = ["| Species | Compartment | Stands for | Value in the SBML at t = 0 (µM) |", "|---|---|---|---|"]
    for s in model.getListOfSpecies():
        start = s.getInitialConcentration() if s.isSetInitialConcentration() else s.getInitialAmount()
        rows.append(f"| `{s.getId()}` | {s.getCompartment()} | {MEANING[s.getId()]} | {start:g} |")
    values = {p.getId(): p.getValue() for p in model.getListOfParameters()}
    reactions = ["| Reaction | What happens | Rate (per compartment volume) | Constants |", "|---|---|---|---|"]
    for r in model.getListOfReactions():
        law = libsbml.formulaToL3String(r.getKineticLaw().getMath())
        used = sorted(set(re.findall(r"\b\w+\b", law)) & set(values))
        constants = ", ".join(f"{n} = {values[n]:g}" for n in used)
        reactions.append(f"| `{r.getId()}` | {_equation(r)} | `{law}` | {constants} |")
    note = (f"\nThe model's own rule `NFKB_total := {rule}` has rate of change identically zero under these reactions "
            "(proved symbolically by the generator), so total NF-κB is conserved.\n")
    return {"species": header + "\n".join(rows) + "\n", "reactions": header + "\n".join(reactions) + "\n" + note}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if a committed table differs")
    args = parser.parse_args()
    for name, text in tables().items():
        if args.check:
            if not OUT[name].exists() or OUT[name].read_text() != text:
                _fail(f"{OUT[name].relative_to(ROOT)} is stale; rerun without --check")
            print(f"{OUT[name].relative_to(ROOT)} is current")
        else:
            OUT[name].write_text(text)
            print(f"wrote {OUT[name].relative_to(ROOT)}")


if __name__ == "__main__":
    main()
