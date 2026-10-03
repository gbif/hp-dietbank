[![GBIF Hosted Portal](https://docs.gbif.org/style/gbif-hosted-portal.svg)](https://github.com/gbif/hosted-portals)
[![Build Status](https://builds.gbif.org/job/hp-dietbank/badge/icon)](https://builds.gbif.org/job/hp-dietbank/lastBuild/console)
<!-- License badge example: [![CC BY-SA 4.0](https://img.shields.io/badge/License-CC%20BY%2D-SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-sa/4.0/) -->

# GBIF Hosted Portal: dietbank

This Jekyll website, **[dietbank (Staging)](https://dietbank.hp.gbif-staging.org/)**, makes use of a theme and biodiversity widgets developed by the GBIF network.

You can find information on editing this site and more on [gbif/hosted-portals](https://github.com/gbif/hosted-portals)

> Powered by [GBIF](https://www.gbif.org/)

## Dietbank specifics

**Diet by host** (`/hosts`) reads a host-species index (`assets/data/hosts*.json`) that is rebuilt after datasets are published. The [Host index workflow](.github/workflows/host-index.yml) rebuilds it:
- every night;
- when started by hand from the Actions tab;
- optionally, when the Dietbank Django app reports a newly registered dataset.

[docs/host-index.md](docs/host-index.md) covers how the index works, how to rebuild it by hand, and how to preview the site locally.

### Releasing

| Site | Updates when | Reads data from |
|---|---|---|
| https://dietbank.hp.gbif-staging.org (staging) | merge to `master` | GBIF.org |
| https://dietbank.hp.gbif-test.org (test) | merge to `master` | gbif-test (the datasets in `_data/test_datasets.yml`) |
| https://dietbank.hp.gbif.org (production) | [GitHub release](https://github.com/gbif/hp-dietbank/releases/new) | GBIF.org |

Keep `_includes/js/config.js` plain JavaScript. GBIF's build syntax-checks it with Node before running Jekyll and aborts on any Liquid. Check it locally with `node --check _includes/js/config.js`.

### Rebuilding the host index after publishing

The nightly run picks up new and changed **GBIF.org** datasets of the Dietbank publisher by itself. Start a rebuild by hand when you don't want to wait, or after registering a **test** dataset, which the nightly run can't discover.

1. Go to [Actions → Host index](https://github.com/gbif/hp-dietbank/actions/workflows/host-index.yml) → **Run workflow**.
2. Choose the environment:
   - `test` for a dataset registered for testing (its key is shown in the Django admin as *GBIF UAT key*);
   - `prod` for a dataset published on GBIF.org;
   - `both` to rebuild everything without a new key.
3. Optionally fill in **dataset_key**. The run then waits until GBIF has indexed that dataset (at least one 5-minute check), and a test key is added to `_data/test_datasets.yml`.
4. The run commits the rebuilt index to `master` only if something changed. GBIF then rebuilds the sites within minutes.

The same from a terminal, with the [GitHub CLI](https://cli.github.com):

```bash
gh workflow run host-index.yml --repo gbif/hp-dietbank -f environment=test -f dataset_key=<key>
```

You need write access to this repository for either route.

GitHub disables scheduled workflows in public repositories after 60 days without repository activity. If the nightly run stops, re-enable it on the workflow page.

#### Optional: automatic trigger from the Django app

The Dietbank Django app can start the same run itself right after registering a dataset. It sends a `repository_dispatch` event, `dietbank-dataset-registered`, with the dataset key and environment (`backend/util/gbif/portal.py`). For that it needs a GitHub token with **Contents: Read and write** on `gbif/hp-dietbank`, set as `PORTAL_GITHUB_TOKEN` on the server.

Tokens for repositories in the `gbif` organisation have to be created or approved by GBIF, so ask helpdesk@gbif.org if you want this. Without the token, the app logs that it skipped the notification and publication carries on. Use the manual run above instead.

### Switching to production (GBIF.org)

Do this once Dietbank publishes to GBIF.org under its own organisation, Conservation Ecology Group, University of Groningen (`aba13a77-07e3-428d-af47-05d98eec61ce`).

**Django app:**
1. Make sure the GBIF Metabarcoding Data Toolkit account in `GBIF_USERNAME` may publish for this organisation. Ask helpdesk@gbif.org if unsure.
2. On the server, set:
   - `GBIF_SANDBOX=False`
   - `GBIF_ORGANIZATION_KEY=aba13a77-07e3-428d-af47-05d98eec61ce`
   - `PORTAL_GITHUB_TOKEN`, if you have one (see above)

   Then restart the app.
3. Publish the studies. The final step stores the GBIF.org key on the study. Then rebuild the index: run the workflow with environment `prod`, or wait for the nightly run. With a token, the app starts the run itself.

**Portal (this repository):**
1. In `_includes/js/config.js`, set `publisherKey` to `aba13a77-07e3-428d-af47-05d98eec61ce`. This changes the occurrence, dataset and literature search scopes. Then remove the duplicate `dietbankPublisherKey`.
2. In `_data/home.yml`, replace `b8323864-602a-4a7d-9127-bb903054e97d` with the Dietbank key in both stat URLs.
3. Replace the placeholder content:
   - `en/home.md` text;
   - collaborators in `en/about.md`;
   - the "Links" menu in `_data/navigation.yml`;
   - `description` in `_config.yml`.
4. Merge to `master` and check staging, which now shows Dietbank data from GBIF.org.
5. Make a GitHub release to update production.

# Guide
This is a Jekyll site using the remote theme gbif/jekyll-hp-base-theme
The theme comes with a site navigation and footer and multilingual support.
There are a set of predefined layouts: `heroImage, page, post, text, documentation, compose`

## Configuring the site navigation
The theme comes with a sit navbar that can be configured in `_data/navigation`. If you have a multilingual site you should provide one per language following the convention `_data/[locale]/navigation.yml`

## Configuring the footer
The theme comes with a sit navbar that can be configured in `_data/footer`. If you have a multilingual site you should provide one per language following the convention `_data/[locale]/footer.yml`

## Multilingual sites
if you have a multilingual site it is recommended that you add a folder in root for each langauge but the default language. Similar in the _posts folder. And in the _data folder. This will make it easier to navigate.

## Layouts

### General parameters for layouts
```yml
layout: heroImage
title: "Your great title"
description: Some description goes here
background: /assets/img/Haeckel_Siphoneae.jpg
imageLicense: Kunstformen der Natur (1904) by Ernst Haeckel via [Wikimedia](https://commons.wikimedia.org/wiki/Kunstformen_der_Natur) # OPTIONAL
cta: # OPTIONAL list of buttons
- text: Optional Call To Action
  href: /link-to-somewhere
  isPrimary: true # OPTIONAL
```

### layout: heroImage
A large image with floating text.

Aside from the general parameters it also takes
```yml
height: 100vh # OPTIONAL- It is possible to control the height of the image. 100vh means that it should take up full Viewport Height (vh)
parallax: true # OPTION - default is false
toc: false # OPTIONAL - default is false. Should the page have a Table of Contents
mobileToc: false # OPTIONAL - default is false. Should the TOC show on mobile devices (will show above article)
```

### layout: post
An title and description with an image underneath

Aside from the general parameters it also takes
```yml
ratio: 40 # OPTIONAL - default is 40. Height in percentage relative to width
toc: true # OPTIONAL - default is false. Should the page have a Table of Contents
mobileToc: false # OPTIONAL - default is false. Should the TOC show on mobile devices (will show above article)
# thumbnail: /assets/images/some-image.jpg # to have more control over how posts appear in cards, then you can overwrite the image using the thumbnail property
```

### layout: documentation
This is useful for navigating large amounts of pages. It displays as a sidebar with nested navigation links. And then a main content.

frontmatter
```yml
layout: documentation
permalink: /layout/documentation # the documentation layout requires you to fill the permalink for it to be highlighted in the side navigation
title: Documentantion layout example
description: The file behind this page can be explored at [`pages/layout/documentation.md`](https://github.com/gbif/jekyll-hp-base-theme/blob/master/pages/layout/documentation.md)
sideNavigation: sideNavigation.guides # A data file describing the sidebar structure
toc: true # optional
```

the sideNavigation.yml could then look like below. The navigation is structured into a group and a list of links below
```yml
guides: # the name we are refering to in the frontmatter. In this example we used fileName.propertyName
- grouptitle: Configuration # first grouping
  content: ## list in  group
  - title: Intro
    path: /documentation-intro
  - title: Translations
    path: /translations
  - sectiontitle: Compositions # second layer group name
    section: # list in second layer
    - title: Hero overlays
      path: /examples/background-overlay
```

## layout: composition
The theme used for your Jekyll site has multiple layouts. But the most important and flexible is the layout we named `compose` which allow you to stich together various configurable blocks. So a page could for example look like
* A hero header with a large image
* A long read (your page markdown)
* Some featured cards with links to other articles.

In the frontmatter for page that would look like
```yml
# use the compose layout for more flexibility
layout: compose
# then define your page composition
composition:
- type: heroImage # block name and in this case the data will be taken from the page frontmatter as nothing else is defined
- type: pageMarkdown # this block will simply render your markdown in this section
- type: features # block name
  data: compose.cardExample # content from the _data folder to fill into the block
```

### Predfined blocks
* heroImage: A large image with floating text
* heroVideo: Same as heroImage but with video
* heroBox: Similar to heroImage but with the text in a white box
* postHeader: title, desctiption and an wide image underneath
* features: title, description and a list of cards with images, title and descriptions
* latestPosts: same as features, but the content comes from the latest _posts
* markdown: define your own markdown
* pageMarkdown: show the markdown from the current page
* splitBanner: image in one side and text in the other. Can be reversed
* textBanner: centered title and description
* stories: configure a news feed that pulls in news stories and more from gbif.org. Will show like a list of card similar to features.
* dashboard: a customisable dashboard (piecharts, barcharts etc) showing data from a subset of gbif.org occurrence data.
* media: a vertical list of image: text pairs. for example a list of pdfs or documents.

Most blocks take the same key:value pairs but just show them differently. Here is the options
```yml
title: supported by all and required by heroImage, heroVideo, heroBox and postHeader
description: Optional
background: /assets/img/Haeckel_Siphoneae.jpg # some url. Ideally the image is in assets as we will then handle scaling the image to different devices.
imageLicense: and optional but recommended license statement
cta: # OPTIONAL list of buttons
- text: Optional Call To Action
  href: /link-to-somewhere
  isPrimary: true # OPTIONAL
features: # features are only used for sub lists. used in features and media blocks
  - preTitle: News  # optional
    title: Abundantly light years # required
    description: some title# required
    background: /assets/img/Haeckel_Caulerpa_racemosa.jpeg # img required
    href: /about # optional link, but makes little sense without
    categories: [cat, dog] # optional tags that will link to the post archives with a filter for that tag. Rarely used
```

The dashboard block also takes
```yml
config: 
  predicate: # a gbif predicate
    type: or
    predicates:
      - type: equals
        key: countryCode
        value: DK
      - type: equals
        key: countryCode
        value: SE
  charts: [iucn, license, basisOfRecord, year, synonyms, iucnCounts, country, continent, dwcaExtension, eventId, gadmGid, mediaType, networkKey, publisherKey, publishingCountryCode, protocol, sampleSizeUnit, samplingProtocol, typeStatus, waterBody, collectionCode, institutionCode, stateProvince, identifiedBy, recordedBy, establishmentMeans, month, preparations, datasetKey, taxa, occurrenceIssue, dataQuality, occurrenceSummary, collectionKey, institutionKey, catalogNumber] # what charts to show
```

### Custom blocks
That structure allow us to do many compositions using the same blocks in various ways. But sometimes the existing blocks does not suffice for your vision. In this case you could create a completely new layout, but decomposing it into reusable blocks that can be used along side the existing blocks is often a better solution.

Place your custom reusable blocks for the `compose` layout in `_includes_/blocks/yourBlockName.html`

### Data layouts
The theme is optimized for exploring subsets of data from gbif.org. For that we have some special layouts that will show that data following the configuration from `_includes/js/config.js`. Those layouts are
* collection-key
* collection-search
* institution-key
* institution-search
* dataset-key
* dataset (which is search despite the name)
* literature (search despite the name)
* occurrence-key
* occurrence (again it is for search)
* publisher-key
* publisher (for search)
* literature (for search)

for those pages it is important to follow the convention that "key" type pages have the permalink /collection/_key_
the reason for that is that _key_ will be replaces on the server to support whatever guid or identifier is provided in the url to load the correct data.
