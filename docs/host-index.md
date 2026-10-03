# Host index: filtering by host species

Dietbank records describe the *prey*. The host species, the organism whose diet sample was analysed, is recorded in `dwc:associatedTaxa` as `host:<scientific name>`. GBIF shows this field on each record but cannot search or filter on it. So the portal ships its own index of hosts, which the **Diet by host** page (`/hosts`) reads.

## Where the index lives

| File | Used by | Built from |
|---|---|---|
| `assets/data/hosts.json` | production and staging | GBIF.org: all datasets of the Dietbank publisher `aba13a77-07e3-428d-af47-05d98eec61ce` |
| `assets/data/hosts-test.json` | test site | gbif-test: the dataset keys passed explicitly |

- Both files are committed to this repository and served as static files.
- GBIF's build (Jenkins) only runs Jekyll; it never rebuilds the index.
- Which file the page loads is set by `dietbank.hostIndex` in `_config.yml` (production) and `_config_test.yml` (test).

Each host entry holds:
- the GBIF filter (predicate) that selects its records: whole datasets where a dataset contains only that host, otherwise that dataset's `eventID`s;
- diet summaries per prey class, order and family:
  - frequency of occurrence: share of samples the prey was detected in;
  - relative read abundance: mean share of a sample's reads.

Because the index is a snapshot, a newly published dataset does not appear on `/hosts` until the index is rebuilt. It does appear in the general occurrence search straight away.

## Rebuilding the index

Normally the [Host index workflow](../.github/workflows/host-index.yml) does this:
- every night;
- when started by hand from the Actions tab;
- optionally, triggered by the Dietbank Django app.

The README explains how to start it by hand. The steps below are the manual fallback, and they describe what the workflow does.

Requirements: Python 3.9 or newer, standard library only, and internet access to the GBIF API.

### Production (GBIF.org)

1. Publish the dataset and wait until GBIF has indexed it. Its records should show on gbif.org with `associatedTaxa` filled in. This usually takes minutes, sometimes a few hours.
2. Rebuild the index. New datasets of the publisher are found automatically:

   ```bash
   python3 scripts/build_host_index.py --publisher aba13a77-07e3-428d-af47-05d98eec61ce
   ```

3. Check the summary it prints on stderr: number of hosts, records without a host, and any warnings.
4. Commit `assets/data/hosts.json` and push. The next portal build puts it live.

Also rebuild after re-publishing a dataset whose samples or hosts changed, or after deleting a dataset.

### Test (gbif-test)

The test publisher is a shared GBIF test organisation, so the test site lists its datasets by key in `_data/test_datasets.yml`. That list limits the test site's occurrence search (see `_includes/head.html`) and tells the script which datasets to read. For a new test dataset:

1. Add its key to `_data/test_datasets.yml`.
2. Rebuild:

   ```bash
   python3 scripts/build_host_index.py --api https://api.gbif-test.org/v1 \
     --dataset-file _data/test_datasets.yml --out assets/data/hosts-test.json
   ```

3. Commit both files.

### Script options

| Option | Default | Purpose |
|---|---|---|
| `--api` | `https://api.gbif.org/v1` | GBIF API to read occurrences from |
| `--publisher KEY` | | include all occurrence and sampling-event datasets of a publisher (repeatable) |
| `--dataset KEY` | | include a dataset (repeatable) |
| `--dataset-file PATH` | | include the datasets listed in a file, one key per line (`- key` YAML list lines work) |
| `--out PATH` | `assets/data/hosts.json` | output file |
| `--relation NAME` | host, host of, eaten by, consumed by, predator, diet of, prey of | `associatedTaxa` relations treated as the host (repeatable) |
| `--allow-bare` | off | treat values without a relation (e.g. just `Ficedula hypoleuca`) as the host |
| `--match-api` | `https://api.gbif.org/v1` | API used to match host names to the GBIF Backbone |

The script reads about 300 records per request. 10,000 records take well under a minute.

### Data requirements

- `associatedTaxa` is `host:<scientific name>`. The forms `"host":"<name>"` and `Host: <name>` also work; separate multiple entries with `|`.
- Each sample (`eventID`) has exactly one host. If a dataset mixes hosts, the filter selects samples by `eventID`, so records without an `eventID` in such a dataset cannot be selected (the script warns about this).
- Read-based metrics need `organismQuantityType` and `sampleSizeUnit` to be `DNA sequence reads`, with `organismQuantity` and `sampleSizeValue` filled in. The GBIF Metabarcoding Data Toolkit produces this by default.

## Previewing the site locally

The system Ruby on macOS is too old, so use Docker.

Production config, which reads from GBIF.org:

```bash
docker compose up --build
```

Test config, which reads from gbif-test and shows the test datasets:

```bash
docker compose run --rm --service-ports portal sh -lc "bundle exec jekyll serve --host 0.0.0.0 --config _config.yml,_config_test.yml"
```

Then open http://localhost:4000/hosts. Changes to files rebuild automatically. Changes to `_config*.yml` need a restart.

## Where changes go live

See *Releasing* in the [README](../README.md#releasing).
