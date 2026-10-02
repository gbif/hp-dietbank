---
lang-ref: hosts
layout: compose
title: Diet by host
description: Explore what each host species eats, based on DNA metabarcoding of diet samples
background: "{{ site.data.images.vliegenvanger.src }}"
imageLicense: "{{ site.data.images.vliegenvanger.caption }}"
height: 40vh
permalink: /hosts
composition:
  - type: heroImage
  - type: hostExplorer
    inlineData:
      intro: |
        Choose a host species to see the prey detected in its diet samples. **Frequency of occurrence** is the share of samples a prey taxon was found in. **Relative read abundance** is the average share of a sample's DNA reads that belong to that prey.

        Host species are taken from the `associatedTaxa` field of each published record.
---
