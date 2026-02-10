---
layout: compose
klass: compositionBlocks
title: Summary of Dietbank data
description: The theme lets you stitch blocks together from the frontmatter. Below is examples of how. See [`pages/compose.md`](https://github.com/gbif/jekyll-hp-base-theme/blob/master/pages/layout/compose.md) for the raw Markdown of this page.
background: /assets/img/Haeckel_Siphoneae.jpg
imageLicense: Kunstformen der Natur (1904) by Ernst Haeckel via [Wikimedia](https://commons.wikimedia.org/wiki/Kunstformen_der_Natur)
hasTextShadow: true
permalink: /summary
config: 
  predicate:
    type: or
    predicates:
      - type: equals
        key: countryCode
        value: DK
      - type: equals
        key: countryCode
        value: SE
  charts: [datasetKey, month, taxa, year]
---
