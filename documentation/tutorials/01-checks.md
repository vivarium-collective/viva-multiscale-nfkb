# 1. Run the checks

Every claim in this documentation rests on a check. Run them all:

```bash
export COMPOSE_API_DIR=/path/to/compose-api
for group in harness kinetic spatial boolean; do bash compose/check.sh $group; done
```

Each case prints a header and then `PASS`, or one `FAIL` line per missed expectation, naming the field, the row, the
value and the expected value.

## Read one check

Open `checks/boolean/pair-nfkb-analytic/`. It holds three things:

- **`case.yaml`:** what is run (`document`, `interval`), what it shows (`description`), and the expectations, each a
  field of the emitter's last row with a tolerance.
- **`document.pbg`:** the process-bigraph composite. It's an ordinary document that compose-api would run as is.
- **The generator:** `checks/boolean/make_pair_nfkb_analytic.py` computes the expected values from the oracle (here,
  the closed form in {doc}`../math/switch`) and writes both files.

## Make it fail

A check is evidence only if it can fail. Copy a case, break one thing, and run it:

```bash
cp -r checks/boolean/pair-nfkb-analytic checks/_try && \
  sed -i.bak 's/"Kv": 5.0/"Kv": 4.0/' checks/_try/document.pbg && \
  bash compose/check.sh _try; rm -rf checks/_try .checks-out/_try
```

With the wrong $K_v$, the adapter computes the wrong `NFKB_total`, `u_NFkB`, `d_NFkB` and P(NFkB on), and each fails.
