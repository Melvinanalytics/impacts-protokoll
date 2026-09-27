# Delivery replay

This bounded replay uses synthetic A01/B01 premises and the existing synthetic O-17 reported-workbook pattern. It creates no customer record and proves no approval, external action, business effect, nontechnical-user success or time saving.

Run from any working directory:

```sh
python /path/to/delivery-replay/replay.py demo
```

The demo uses temporary files and separate Python invocations. To continue a workspace across invocations, run `init --workspace PATH`, then `resume --workspace PATH`; revise the synthetic material-ready snapshot with `revise-material --workspace PATH --date YYYY-MM-DD`, then run `resume` again. `state.json` preserves replay outputs for continuation; it is not an authority record.

## Boundaries

- Sales `kennzahl:lieferzeit` means calendar days from accepted order to customer-confirmed arrival. Production `kennzahl:lieferzeit` means machine hours from released order to completed assembly. They live in separate synthetic namespaces. The replay has no inputs that calculate either value.
- B01's R7 rule and personal-workbook practice remain separate. The replay executes R7 only. It does not inspect or compare a workbook.
- O-17's 12-calendar-day workbook display stays a `reported` claim from the existing example. Its formula remains `open`; it is not attributed to B01's formula.
- The R7 output is a candidate estimated date from declared synthetic snapshots. It is not an accepted date or customer commitment. A human decision remains `open`; commitment stays blocked.
- `inputs.sha256.json` detects byte changes to its listed inputs while that manifest stays unchanged. The manifest is not signed. Rewriting both input and digest can pass; that is outside this check's guarantee. Source authority, freshness and truth are not established by a digest. `state.json` is outside the input manifest.

The weekday calendar is a declared synthetic fixture convention: Monday through Friday, with holidays omitted. All dates and values exist only to execute the fixed example deterministically.
