# CLAUDE.md — hp-dietbank

GBIF hosted portal for **Dietbank**: a repository of prey taxa detected by DNA metabarcoding in diet samples (faeces, gut contents) of predators/hosts — insects, birds, mammals, fish. Jekyll site on the remote theme `gbif/jekyll-hp-base-theme`, built and deployed by GBIF (Jenkins: https://builds.gbif.org/job/hp-dietbank/).

- Sites: staging https://dietbank.hp.gbif-staging.org/ (`_config_staging.yml`, GBIF.org data) and test https://dietbank.hp.gbif-test.org/ (`_config_test.yml`, gbif-test data) rebuild on commits to `master`. Production (https://dietbank.hp.gbif.org/) updates on a GitHub release. See the table in `docs/host-index.md`.
- General theme/layout/block docs: `README.md` and `.github/copilot-instructions.md` (accurate; read them instead of re-exploring). Theme docs: https://hp-theme.gbif-staging.org/documentation-intro

## Current state (as of 2026-10-02)

- Early prototype. Most copy is placeholder (lorem ipsum in `en/home.md`, fake collaborators in `en/about.md`, template links in `_data/navigation.yml` "Links" menu, placeholder `description` in `_config.yml`).
- **Data scope is a deliberate stand-in** (an unrelated large dataset with no host info, used for testing the widgets). `_includes/js/config.js` and `_data/home.yml` scope to `publisherKey = b8323864-…` = *SLU Artdatabanken* (Sweden, ~123M records). The real Dietbank publisher is `dietbankPublisherKey = aba13a77-07e3-428d-af47-05d98eec61ce` (Conservation Ecology Group, University of Groningen), which has **0 datasets on GBIF prod, UAT and test** so far. Switch the scope once data is published. The production checklist is in the README.
- `en/data/summary.md` is a dashboard with a placeholder DK/SE country predicate.
- Only English (`en/`) exists, though `config.js` declares Danish and `_config.yml` has defaults for many languages.
- Disabled widget pages live in `en/data/disabled/` (excluded in `_config.yml`).

## Building locally

System Ruby (2.6) is too old. Use Docker (Jekyll 4.1, gems from GBIF mirror):

```bash
docker compose up --build   # serves http://localhost:4000 with --watch
```

There are no tests/linters; "it builds and renders" is the check. Data widgets load client-side from GBIF APIs, so pages work offline only partially. `_key_` detail pages (`/occurrence/_key_`) are rewritten server-side by GBIF; locally open them via the search page.

## Where things live

- `_includes/js/config.js` — `siteConfig` for the GBIF widget library (v3, `useSharedLibrary: true`): enabled pages, scopes (occurrence scope uses GBIF predicate format), highlighted/excluded filters, tabs, map, languages. Source of truth for data behaviour. **Keep it plain JavaScript, with no Liquid:** GBIF's build runs a Node syntax check on it before Jekyll and aborts on failure. Check it with `node --check _includes/js/config.js`. Do environment-specific overrides in `_includes/head.html`, which loads after `config.js` and before the widgets start.
- `_data/*.yml` — navigation, footer, home stats (`home.yml`), images, translations.
- `_includes/blocks/` — custom compose blocks (`{{ include.content.* }}`), e.g. `hostExplorer.html`. `_layouts/` — overrides of theme layouts; empty.
- `_sass/_main.scss` imports theme + `_example.scss`. Brand primary `#fa5e97` (site) vs widget theme primary `#001972` in `config.js`.

## Domain notes: host species

- **Host species filter** (the organism whose diet was sampled). In Darwin Core each record's `scientificName` is the *prey*; the host is in `dwc:associatedTaxa` as `host:<scientific name>` (as produced by the GBIF Metabarcoding Data Toolkit). GBIF returns `associatedTaxa` on records but does **not** index it: the occurrence API ignores the parameter, GraphQL rejects it (`INVALID_PREDICATE`), and it can't be faceted. The same goes for DNA-extension `specific_host` and Humboldt `targetTaxonomicScope`. We decided not to misuse indexed fields (organismID, fieldNumber, …).
- **How it works:** `scripts/build_host_index.py` (stdlib Python) pages all records, parses hosts, matches them to the GBIF Backbone, and writes a static index: `assets/data/hosts.json` (GBIF.org, Dietbank publisher) and `assets/data/hosts-test.json` (gbif-test datasets listed in `_data/test_datasets.yml`). Each host entry has a precomputed GBIF predicate: whole `datasetKey`s for single-host datasets, `datasetKey` AND `eventId` list otherwise. This assumes one host per eventID. Each entry also has diet summaries per prey class/order/family (FOO = share of samples; RRA = mean reads/sampleSizeValue).
- **Rebuilding the index:** `.github/workflows/host-index.yml` handles it. It runs on `repository_dispatch` `dietbank-dataset-registered` from the Django app (`~/Projects/dietbank`, `backend/util/gbif/portal.py`; payload `dataset_key`, `environment` test|prod, `study_id`), nightly, and by hand. It waits for GBIF indexing, appends new test keys to `_data/test_datasets.yml`, and commits only on content changes, ignoring the `generated` timestamp. GBIF's Jenkins only runs Jekyll. The human-facing procedure is in `docs/host-index.md`; keep it in sync when changing the script or config.
- `/hosts` page (`en/data/hosts.md`) uses the custom block `_includes/blocks/hostExplorer.html` and styles in `_sass/_hostExplorer.scss`. The block has a host picker (`?host=` deep link), a custom bar chart with table toggle, links to `/occurrence/search?predicate=<json>&view=table|map|download`, and a GBIF `renderDashboard` filtered by the host predicate. The `predicate` URL filter only exists in the v3 lib (2026-05+). In the search UI it shows as "Complex query".
- **Per-environment config:** `site.dietbank.hostIndex`, and `site.dietbank.scopeDatasets` (test only), which names `_data/test_datasets.yml`. `_includes/head.html` uses that list to override the `config.js` occurrence scope at runtime. `_config_test.yml` also loads `https://www-lib.gbif-test.org/gbif-lib.js`; that lib build reads from gbif-test, while the staging/prod libs read from api.gbif.org.
- Local check against test data: `docker compose run --rm --service-ports portal sh -lc "bundle exec jekyll serve --host 0.0.0.0 --config _config.yml,_config_test.yml"`.
