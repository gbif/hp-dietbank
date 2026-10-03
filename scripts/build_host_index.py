#!/usr/bin/env python3
"""Build the host-species index used by the "Diet by host" page.

GBIF returns dwc:associatedTaxa on every occurrence but does not index it for
search, so the portal cannot filter on it directly. This script pages through
all Dietbank occurrences, groups them by host (parsed from associatedTaxa), and
writes a static JSON file with, per host:

  - the GBIF occurrence predicate that selects exactly that host's records
    (whole datasets where a dataset has only that host, otherwise the
    dataset's eventIDs), used to filter the standard occurrence search and
    dashboard widgets;
  - diet summaries per prey class/order/family: frequency of occurrence
    (share of samples the prey was detected in) and mean relative read
    abundance (reads / sample reads, averaged over samples).

Only the Python standard library is needed. Examples:

  # the test datasets on gbif-test
  python3 scripts/build_host_index.py --api https://api.gbif-test.org/v1 \
      --dataset-file _data/test_datasets.yml --out assets/data/hosts-test.json

  # everything published by Dietbank on GBIF.org
  python3 scripts/build_host_index.py --publisher aba13a77-07e3-428d-af47-05d98eec61ce
"""

import argparse
import collections
import datetime
import json
import re
import sys
import time
import urllib.parse
import urllib.request

PAGE_SIZE = 300
MAX_OFFSET = 100_000  # GBIF occurrence search paging limit per query
READS_TYPE = "dna sequence reads"
DEFAULT_RELATIONS = ["host", "host of", "eaten by", "consumed by", "predator", "diet of", "prey of"]
PREY_RANKS = ["class", "order", "family"]
TOP_N = 30  # prey taxa kept per rank, metric and host


def get_json(url, retries=4):
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=60) as res:
                return json.load(res)
        except Exception as e:  # noqa: BLE001 - retry on any network/HTTP error
            if attempt == retries - 1:
                raise
            print(f"  retry {url}: {e}", file=sys.stderr)
            time.sleep(2 ** attempt)


def search_url(api, **params):
    return f"{api}/occurrence/search?" + urllib.parse.urlencode(params, doseq=True)


def iter_occurrences(api, dataset_key):
    """Yield all occurrences of a dataset, splitting by year if it exceeds the paging limit."""
    total = get_json(search_url(api, datasetKey=dataset_key, limit=0))["count"]
    if total <= MAX_OFFSET:
        slices = [{}]
    else:
        facets = get_json(search_url(api, datasetKey=dataset_key, limit=0, facet="year", facetLimit=1000))
        years = [c["name"] for f in facets["facets"] for c in f["counts"]]
        slices = [{"year": y} for y in years]
        # records without a year are not reachable via year slices
        print(f"  {dataset_key}: {total} records, paging per year ({len(years)} years)", file=sys.stderr)
    for extra in slices:
        offset = 0
        while True:
            page = get_json(search_url(api, datasetKey=dataset_key, limit=PAGE_SIZE, offset=offset, **extra))
            yield from page["results"]
            offset += PAGE_SIZE
            if page["endOfRecords"] or offset >= MAX_OFFSET:
                break


ENTRY_SPLIT = re.compile(r"\s*\|\s*")
QUOTED = re.compile(r'"([^"]+)"\s*:\s*"([^"]+)"')
PLAIN = re.compile(r"^\s*([^:]+?)\s*:\s*(.+?)\s*$")


def parse_hosts(associated_taxa, relations, allow_bare):
    """Return host names from a dwc:associatedTaxa value.

    Supports the DwC-recommended form '"host":"Name"' as well as 'host: Name'
    and 'host:Name', with multiple entries separated by '|'.
    """
    if not associated_taxa:
        return []
    hosts = []
    for entry in ENTRY_SPLIT.split(associated_taxa.strip()):
        pairs = QUOTED.findall(entry)
        if not pairs:
            m = PLAIN.match(entry)
            pairs = [(m.group(1), m.group(2))] if m else [(None, entry)]
        for relation, name in pairs:
            name = name.strip().strip('"').strip()
            if not name:
                continue
            if relation is None:
                if allow_bare:
                    hosts.append(name)
            elif relation.strip().lower() in relations:
                hosts.append(name)
    return hosts


def match_host(name, match_api):
    """Match a host name against the GBIF Backbone to get its taxonomy."""
    m = get_json(f"{match_api}/species/match?" + urllib.parse.urlencode({"name": name}))
    if m.get("matchType") == "NONE":
        return {}
    keys = ["usageKey", "canonicalName", "rank", "kingdom", "phylum", "class", "order", "family", "genus"]
    return {k: m.get(k) for k in keys if m.get(k) is not None}


def summarise(records, rank_fields):
    """Diet summary for one host: FOO and mean RRA per prey taxon and rank."""
    samples = {}  # sample id -> sample reads
    for r in records:
        sid = r["_sample"]
        size = r.get("sampleSizeValue") if (r.get("sampleSizeUnit") or "").lower() == READS_TYPE else None
        samples.setdefault(sid, size)
    n_samples = len(samples)

    out = {}
    for rank in rank_fields:
        per_taxon = collections.defaultdict(lambda: {"samples": set(), "records": 0, "reads": collections.Counter()})
        for r in records:
            name = r.get(rank) or "Unassigned"
            t = per_taxon[(name, r.get(rank + "Key"))]
            t["samples"].add(r["_sample"])
            t["records"] += 1
            if (r.get("organismQuantityType") or "").lower() == READS_TYPE and r.get("organismQuantity") is not None:
                t["reads"][r["_sample"]] += r["organismQuantity"]
        rows = []
        for (name, key), t in per_taxon.items():
            rra = [t["reads"][s] / samples[s] for s in samples if samples[s]]
            rows.append({
                "name": name,
                "key": key,
                "records": t["records"],
                "samples": len(t["samples"]),
                "foo": round(len(t["samples"]) / n_samples, 4) if n_samples else 0,
                "rra": round(sum(rra) / len(rra), 4) if rra else None,
            })
        # keep the top taxa by occurrence and by read abundance, so either ranking is complete
        by_foo = sorted(rows, key=lambda x: (-x["samples"], -x["records"]))[:TOP_N]
        by_rra = sorted(rows, key=lambda x: -(x["rra"] or 0))[:TOP_N]
        out[rank] = list({id(x): x for x in by_foo + by_rra}.values())
    return n_samples, out


def build_predicate(dataset_hosts, host, host_datasets, events):
    """Predicate selecting a host's records: whole datasets where possible, else eventIDs."""
    whole = sorted(k for k in host_datasets if dataset_hosts[k] == {host})
    parts = []
    if whole:
        parts.append({"type": "in", "key": "datasetKey", "values": whole})
    for k in sorted(events):
        if k in whole:
            continue
        parts.append({"type": "and", "predicates": [
            {"type": "equals", "key": "datasetKey", "value": k},
            {"type": "in", "key": "eventId", "values": sorted(events[k])},
        ]})
    return parts[0] if len(parts) == 1 else {"type": "or", "predicates": parts}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--api", default="https://api.gbif.org/v1", help="GBIF API v1 base (default: %(default)s)")
    p.add_argument("--match-api", default="https://api.gbif.org/v1", help="API used to match host names to the GBIF Backbone")
    p.add_argument("--publisher", action="append", default=[], help="publishingOrg key (repeatable)")
    p.add_argument("--dataset", action="append", default=[], help="dataset key (repeatable)")
    p.add_argument("--dataset-file", help="file with one dataset key per line, optionally as a YAML list ('- key')")
    p.add_argument("--relation", action="append", help=f"associatedTaxa relation(s) treated as host (default: {DEFAULT_RELATIONS})")
    p.add_argument("--allow-bare", action="store_true", help="treat associatedTaxa values without a relation as host")
    p.add_argument("--out", default="assets/data/hosts.json")
    args = p.parse_args()

    relations = {r.lower() for r in (args.relation or DEFAULT_RELATIONS)}
    dataset_keys = list(args.dataset)
    if args.dataset_file:
        with open(args.dataset_file) as f:
            for line in f:
                line = line.split("#", 1)[0].strip().removeprefix("-").strip()
                if line:
                    dataset_keys.append(line)
    for org in args.publisher:
        offset = 0
        while True:
            page = get_json(f"{args.api}/dataset/search?publishingOrg={org}&type=OCCURRENCE&type=SAMPLING_EVENT&limit=100&offset={offset}")
            dataset_keys += [d["key"] for d in page["results"]]
            offset += 100
            if page["endOfRecords"]:
                break
    if not (args.dataset or args.dataset_file or args.publisher):
        p.error("pass --dataset, --dataset-file and/or --publisher")

    by_host = collections.defaultdict(list)
    dataset_hosts = collections.defaultdict(set)
    datasets = {}
    no_host = 0
    for key in dict.fromkeys(dataset_keys):
        meta = get_json(f"{args.api}/dataset/{key}")
        datasets[key] = {"key": key, "title": meta.get("title")}
        n = 0
        for r in iter_occurrences(args.api, key):
            n += 1
            hosts = parse_hosts(r.get("associatedTaxa"), relations, args.allow_bare)
            if not hosts:
                no_host += 1
                dataset_hosts[key].add(None)
                continue
            r["_sample"] = f"{key}/{r.get('eventID') or r.get('materialSampleID') or r['key']}"
            for h in dict.fromkeys(hosts):
                by_host[h].append(r)
                dataset_hosts[key].add(h)
        print(f"{key}: {n} records ({datasets[key]['title']})", file=sys.stderr)

    hosts = []
    for name, records in sorted(by_host.items()):
        events = collections.defaultdict(set)
        per_dataset = collections.Counter()
        for r in records:
            per_dataset[r["datasetKey"]] += 1
            if r.get("eventID"):
                events[r["datasetKey"]].add(r["eventID"])
        # only a problem where the dataset also holds other hosts (then eventIDs are needed)
        missing_event = sum(1 for r in records if not r.get("eventID") and dataset_hosts[r["datasetKey"]] != {name})
        n_samples, diet = summarise(records, PREY_RANKS)
        years = sorted({r["year"] for r in records if r.get("year")})
        hosts.append({
            "name": name,
            "taxon": match_host(name, args.match_api),
            "records": len(records),
            "samples": n_samples,
            "datasets": [{**datasets[k], "records": c} for k, c in per_dataset.most_common()],
            "countries": sorted({r["country"] for r in records if r.get("country")}),
            "years": [years[0], years[-1]] if years else None,
            "predicate": build_predicate(dataset_hosts, name, per_dataset, events),
            "recordsWithoutEventId": missing_event,
            "diet": diet,
        })
        if missing_event:
            print(f"warning: {missing_event} records of host {name!r} have no eventID and can only be "
                  f"in mixed-host datasets and cannot be selected by the host filter", file=sys.stderr)

    out = {
        "generated": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "api": args.api,
        "datasets": len(datasets),
        "recordsWithoutHost": no_host,
        "hosts": hosts,
    }
    with open(args.out, "w") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"wrote {args.out}: {len(hosts)} hosts, {no_host} records without host", file=sys.stderr)


if __name__ == "__main__":
    main()
