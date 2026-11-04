# Atlas clickable product prototype

Open `index.html` in a browser. The prototype is dependency-free HTML/CSS/JavaScript.

## Try the intended onboarding journey

1. Select **Connect source**.
2. Choose **S3**, **PostgreSQL**, or **Local fixture**.
3. Enter a *display-only* connection name, illustrative source location, and scope.
4. Review a seeded discovery preview and add the sample source.
5. Select **Pipeline**, start a simulated run, and click stages for explanations.
6. Select **Search lab** to inspect seeded results and document provenance.

### Safety and scope

This is **not a production UI**. It makes **no network requests**, does not validate credentials, does not connect to source databases, does not invoke AI, and does not persist user input. Never enter real credentials in the prototype. Metrics and results are simulated to validate product flow.

The implementation plan and actual contracts are documented in [Source-first architecture](../docs/SOURCE_FIRST_ARCHITECTURE.md).

## Proposed real UI boundaries

- Connector wizard must call a backend to validate credentials securely and read source catalog.
- Preview must show real normalized documents and mapping errors.
- Pipeline stage state must be driven by durable run/job records and event streams.
- Search must be backed by Milvus with authorization and authoritative PostgreSQL document-state checks.
- AI suggestions must be labeled, reviewable, and not execute destructive actions without approval.
