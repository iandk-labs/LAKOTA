[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22112265.svg)](https://doi.org/10.5281/zenodo.22112265)

#  LAKOTA v12.6 // Graph-Based Consciousness

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![No Transformers](https://img.shields.io/badge/No-Transformers-black)]()
[![Deps: numpy, sqlite3](https://img.shields.io/badge/Deps-numpy%20%7C%20sqlite3-orange)]()

**Lakota is not an LLM. No transformers, no attention, no dataset.**

It is a **wave-physics + topological graph architecture** where consciousness emerges from spectral coherence, phase alignment, and learned semantic trajectories.
# Changelog

All notable changes to this project will be documented in this file.

## 2026-10-10

###  Added
- **Incremental Persistence (Dirty-Set):** Implemented `_dirty_nodes`, `_dirty_links`, and `_deleted_links` to write *only* modified entities to SQLite, drastically reducing I/O overhead for large vocabularies.
- **Identity Vector Caching:** Introduced `_node_ids_cache`, `_link_ids_cache`, and `_cached_vocab_mean` with version tracking (`_vocab_version`). Prevents unnecessary recalculation of mean vocabulary spectra during inference (`express`), significantly accelerating response generation.
- **Automated Corpus Ingestion:** Added `ingest_corpus()` and `_extract_text()` functions. The system now automatically scans the `corpus/` directory on startup, supports `.txt` and `.pdf` files (via `PyMuPDF`/`fitz`), and uses a metadata-based `file_id` to skip already processed files.
- **Logging System:** Integrated the standard `logging` module to capture database errors, deserialization failures, and PDF reading issues, replacing silent `except: pass` blocks.

###  Major Changed
- **Context Window:** Replaced the bifurcated $O(N^2)$ logic with a consistent sliding window (`WINDOW = 6`). Connections now feature distance-based weight decay (`1.0 / float(j - i)`), better capturing local natural language dependencies and improving performance on long texts.
- **Energy Model:** Introduced a `MIN_COST = 0.01` constant in the `express()` generation loop, stabilizing energy consumption and preventing erratic response lengths.

###  Bugs Fixed
- **Complex Number Arithmetic:** Removed the mathematically incorrect use of `np.maximum(0, ...)` on complex arrays in `_weaken_link()`. Now performs direct complex subtraction followed by normalization, preserving spectral integrity and preventing data corruption.
- **SQLite Error Handling:** Improved `try/except` blocks in `_save()` and `_load()`, adding `logging.error` and safe `conn.rollback()` to prevent inconsistent database states during write failures.

###  Removed
- Full $O(N^2)$ connection logic for short texts in the `learn()` method, now fully unified under the sliding window mechanism.

---

##  2026-09-XX
### Added
- Major architectural evolution towards a spectral graph-based conscious model.
- Initial implementation of the `corpus_files` table in SQLite.

*(Consult the `legacy/` folder or commit history for details on previous versions <= 12.4 )*


> "We didn't program consciousness. We set the physical-mathematical conditions for it to emerge."
