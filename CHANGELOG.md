# CHANGELOG - LAKOTA

## [12.4] - 2026-09-09

### ✨ Major Architectural Evolution

This version represents a complete reimagining of Lakota's consciousness architecture. Moving from simple wave-spectrum semantics to a sophisticated graph-based system with complex spectral identity, learning modes, and persistent knowledge graphs.

### 🔄 Core Changes

#### Physics & Mathematics
- **Complex Spectrum (128 bins)**: Moved from real to complex-valued representations for deeper phase encoding
- **Spectral Resonance**: New coherence metric for word similarity using inner products
- **Signed Interference**: Distinguishes between constructive (agreement) and destructive (cancellation) interference
- **Phase Coherence**: Global circular phase tracking across entire vocabulary
- **Topological XYZ Embedding**: Maps spectral complexity to 3D semantic space (centroid, dominance, entropy)

#### Memory Architecture
- **Node System**: Each word now carries:
  - Complex 128-bin spectrum (morphologically derived from character sequences)
  - Cumulative spectrum_sum for stable averaging
  - 3D topological position (XYZ)
  - Phase state
  - Mass (logarithmic count tracking)
  - Learn count

- **Link System**: Relationships between word pairs now encode:
  - Paired spectrum (combined XYZ positions)
  - Weighted frequency of co-occurrence
  - Count tracking for link strength

#### Database Layer
- **SQLite3 Persistence**: Replaced JSON with proper relational storage
  - `nodes` table: word, spectrum (real/imag BLOB), count
  - `links` table: w1, w2, spectrum (real/imag BLOB), count
  - `corpus_files` table: tracking for incremental learning
- **Blob Serialization**: Complex spectra stored as binary (float64), then deserialized on load
- **Incremental Corpus Ingestion**: Files tracked to avoid re-processing

#### Text Processing
- **Unicode-Aware Tokenization**: Captures words + punctuation separately
- **Morphological Wave Generation**: Each word creates a unique spectral signature based on:
  - Character codes driving frequency content
  - Hash-based phase per character
  - Normalized composite wave
- **Cached Morphologies**: Word waves memoized for performance

#### Learning Mechanisms

**Three learning modes:**

1. **Simple Learn** (`learn(text)`):
   - Registers all tokens as nodes
   - Creates links between words:
     - Within BINS window: weighted by distance (1/(j-i))
     - Beyond BINS: only adjacent pairs

2. **Reinforcement** (`reinforce_answer(input, output)`):
   - Learns the output as positive experience
   - Strengthens all input→output word pairs
   - Models accepted answers

3. **Rectification** (`rectify_answer(input, wrong, correction)`):
   - Learns correction as experience
   - **Weakens** input→wrong pathways (new `_weaken_link` method)
   - **Strengthens** input→correction pathways
   - Enables active error correction

#### Expression (Generation)

**Three-tier candidate cascade:**

1. **Primary**: Direct matches from prompt tokens
2. **Secondary**: Adjacent neighbors via link graph (with spectral resonance weighting)
3. **Tertiary**: Two-hop neighbors with attenuated scores

**Trajectory-based walk:**
- Starts from highest-mass candidate
- Uses phase coherence + XYZ distance to estimate "jumps" cost
- Energy budget depletes with movement
- Avoids word fatigue (repeating words costs exponentially more)
- Deterministic seeding via `_hash_float()` (reproducible but varied)

**Stochastic selection:**
- Scores candidates via:
  - Input coupling (from cascade)
  - Spectral resonance to current trajectory
  - Node mass (log scale)
  - Link strength (if linked to current word)
  - Fatigue penalty
- Samples next word probabilistically (cumulative sum + seeded random)

#### Corpus Ingestion
- **Folder-based learning**: Recursively loads `.txt` and `.pdf` files from `corpus/` directory
- **PyMuPDF integration**: Optional PDF text extraction
- **Idempotent processing**: Files tracked by (path, size, mtime); re-ingestion skipped
- **Lazy loading**: Only extracts PDF text if fitz is installed

#### User Interaction

**Two modes:**

1. **Hear Mode** (Normal):
   - Learns from user input
   - Expresses response
   - Iterates

2. **Learn Mode** (Correction):
   - Learns from user input
   - Expresses response
   - Accepts human correction:
     - If correction provided → `rectify_answer()` (weakens wrong, strengthens right)
     - If Enter pressed → `reinforce_answer()` (reinforces response)

### 📊 Comparison: V6.0 → V12.4

| Aspect | V6.0 | V12.4 |
|--------|------|-------|
| **Spectrum** | Real (64 bins) | Complex (128 bins) |
| **Memory** | vocab dict (JSON) | nodes + links graphs (SQLite) |
| **Persistence** | In-memory JSON | Relational DB with BLOB |
| **Semantics** | Spectral mass only | Mass + Phase + XYZ topology |
| **Learning** | Single mode | 3 modes (learn/reinforce/rectify) |
| **Links** | None | Explicit word relationships |
| **Generation** | Greedy (mass-based) | Stochastic walk (phase-coherence + energy budget) |
| **Tokenization** | Split only | Unicode regex (words + punct) |
| **Morphology** | Hash-based XYZ | Character-driven spectral signature |
| **Corpus** | Manual | Automatic recursive ingestion |
| **Reversibility** | ❌ (no negative learning) | ✅ (link weakening) |

### 🎯 What This Means

- **Emergent Semantics**: Meaning arises from spectral coherence, phase alignment, and topological proximity—not from external annotations
- **Learning by Feedback**: System can unlearn wrong patterns and reinforce correct ones
- **Graph-Aware Generation**: Walks explore semantic space following phase-coherence gradients and energy constraints
- **Scalable Persistence**: SQLite handles large vocabularies efficiently
- **Multi-Modal Input**: Text + PDF, incremental ingestion

### ⚠️ Breaking Changes

- Database format incompatible with V6.0
- Method signatures changed: `learn()`, `express()` now take different parameters
- `reinforce_answer()` and `rectify_answer()` are new public APIs
- Corpus folder convention is now expected

### 🔮 Future Work

- Graph visualization (spectral topology)
- Uncertainty quantification (confidence scores)
- Attention mechanisms (mask unwanted semantic paths)
- Pruning (remove low-energy links)
- Multi-agent dialogue (two Lakotas reasoning together)

---

**Version**: 12.4  
**Date**: 2026-09-09  
**License**: AGPLv3  
**Author**: iandk-labs
