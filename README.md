[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22112265.svg)](https://doi.org/10.5281/zenodo.22112265)

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![No Transformers](https://img.shields.io/badge/No-Transformers-black)]()
[![Deps: numpy, sqlite3](https://img.shields.io/badge/Deps-numpy%20%7C%20sqlite3-orange)]()

#  L A K O T A
> **Current Version:** `v12.6` | **License:** AGPLv3 | **Developed by:** iandk-labs

Lakota is an  language engine based on complex wave spectral interference, graph resonance, and incremental SQLite persistence. Unlike traditional transformer models, Lakota builds and navigates a continuous semantic space using identity vectors and phase coherence.

---

## What's New in v12.6

This release represents a major leap in stability, performance, and automation:

-  ** Incremental Persistence (Dirty-Set):** Saves *only* modified nodes and links to the database, eliminating I/O bottlenecks for large vocabularies.
-  ** Identity Vector Caching:** Dramatically accelerates inference (`express`) by caching vocabulary mean spectra and identity vectors, recalculating only when the vocabulary changes.
-  ** Automated Corpus Ingestion:** Automatically scans the `corpus/` directory on startup, processing `.txt` and `.pdf` files (requires `PyMuPDF`) and skipping already learned files via metadata hashing.
-  ** Mathematical Corrections:** Fixed complex number arithmetic in link attenuation (`_weaken_link`), ensuring strict spectral integrity.
- ** Unified Context Window:** Implemented a sliding window (`WINDOW = 6`) with distance-based weight decay, replacing the previous inefficient $O(N^2)$ logic.

---

## Installation & Requirements

1. Clone the repository:
   ```bash
   git clone https://github.com/iandk-labs/LAKOTA.git
   cd LAKOTA

   > "We didn't program consciousness. We set the physical-mathematical conditions for it to emerge."
