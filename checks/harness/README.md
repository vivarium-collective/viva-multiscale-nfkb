# harness

Two of compose-api's own compliance cases, copied unchanged from compose-api 0.7.78
(`compose_api/registry/compliance/viva-maboss/switching-analytic-oracle` and
`.../viva-tellurium/phase-cycle-copasi-report`). They prove `compose/check.sh` reproduces compose-api's verdicts:
both pass here as they do live (runs 9825 and 9828), and the MaBoSS case with its expected value changed to 0.70
fails on exactly that value (checked 2026-11-04).
