# -*- coding: utf-8 -*-
"""
L A K O T A v12.4
License: AGPLv3
iandk-labs

"""

import re
import math
import time
import sqlite3
import hashlib
import numpy as np
from pathlib import Path


EPS = 1e-12
BINS = 128
CORPUS_DIR = Path("corpus")


class Lakota:

    def __init__(self, path="lakota.db"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

        self.nodes = {}
        self.links = {}
        self._wave_cache = {}

        self.conn = sqlite3.connect(str(self.path))
        self._ensure_tables()
        self._load()

    # ==================================================================
    # CLOSE
    # ==================================================================

    def close(self):
        try:
            self.conn.commit()
            self.conn.close()
        except Exception:
            pass

    # ==================================================================
    # DB
    # ==================================================================

    def _ensure_tables(self):
        cur = self.conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS nodes(
                word TEXT PRIMARY KEY,
                real BLOB NOT NULL,
                imag BLOB NOT NULL,
                count INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS links(
                w1 TEXT NOT NULL,
                w2 TEXT NOT NULL,
                real BLOB NOT NULL,
                imag BLOB NOT NULL,
                count REAL NOT NULL DEFAULT 0.0,
                PRIMARY KEY(w1, w2)
            );

            CREATE TABLE IF NOT EXISTS corpus_files(
                file_id TEXT PRIMARY KEY,
                ingested_at REAL
            );
        """)
        self.conn.commit()

    def _complex_to_blobs(self, spectrum):
        spectrum = np.asarray(spectrum, dtype=complex)
        real = np.real(spectrum).astype(np.float64).tobytes()
        imag = np.imag(spectrum).astype(np.float64).tobytes()
        return real, imag

    def _blob_to_complex(self, real_blob, imag_blob):
        try:
            real = np.frombuffer(real_blob, dtype=np.float64).copy()
            imag = np.frombuffer(imag_blob, dtype=np.float64).copy()

            if len(real) != BINS or len(imag) != BINS:
                return None

            return real + 1j * imag
        except Exception:
            return None

    def _mark_file(self, file_id):
        self.conn.execute(
            "INSERT OR REPLACE INTO corpus_files(file_id, ingested_at) VALUES(?, ?)",
            (file_id, time.time())
        )
        self.conn.commit()

    # ==================================================================
    # TEXT
    # ==================================================================

    def _tokenize(self, text):
        """
        Captures words and punctuation marks as separate tokens.
        Preserves uppercase and lowercase.
        """
        if not text:
            return []

        return re.findall(r"\w+|[^\w\s]", text, flags=re.UNICODE)

    def _words(self, text):
        """
        Returns only word tokens.
        Preserves uppercase and lowercase.
        """
        return [
            token for token in self._tokenize(text)
            if re.match(r"\w+", token, flags=re.UNICODE)
        ]

    # ==================================================================
    # MATH
    # ==================================================================

    def _normalize(self, spectrum):
        spectrum = np.asarray(spectrum, dtype=complex)
        norm = np.linalg.norm(spectrum)

        if norm < EPS:
            return np.zeros(BINS, dtype=complex)

        return spectrum / norm

    def _spectral_resonance(self, a, b):
        a = np.asarray(a, dtype=complex)
        b = np.asarray(b, dtype=complex)

        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a < EPS or norm_b < EPS:
            return 0.0

        value = float(np.abs(np.sum(a * np.conj(b)))) / (norm_a * norm_b)
        return max(0.0, min(1.0, value))

    def _signed_interference(self, a, b):
        """
        Signed interference:
          positive = agreement
          negative = cancellation
        """
        a = np.asarray(a, dtype=complex)
        b = np.asarray(b, dtype=complex)

        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a < EPS or norm_b < EPS:
            return 0.0

        value = float(np.real(np.sum(a * np.conj(b)))) / (norm_a * norm_b)
        return max(-1.0, min(1.0, value))

    def _phase_from_spectrum(self, spectrum):
        """
        Global circular phase.
        """
        spectrum = np.asarray(spectrum, dtype=complex)
        weights = np.abs(spectrum)
        total = float(np.sum(weights))

        if total < EPS:
            return 0.0

        angles = np.angle(spectrum)
        vec = np.sum(weights * np.exp(1j * angles))

        if np.abs(vec) < EPS:
            return 0.0

        return (np.angle(vec) % (2.0 * math.pi)) / (2.0 * math.pi)

    def _phase_coherence(self, phase1, phase2):
        delta = abs(phase1 - phase2)
        return math.cos(2.0 * math.pi * delta)

    def _hash_int(self, *parts):
        seed = "|".join(repr(p) for p in parts).encode("utf-8")
        h = hashlib.sha3_256(seed).hexdigest()
        return int(h[:8], 16)

    def _hash_float(self, *parts):
        return self._hash_int(*parts) / float(2 ** 32)

    # ==================================================================
    # MORPHOLOGIC SIGNAL
    # ==================================================================

    def _word_wave(self, word):
        """
        Morphological wave sensitive to uppercase and lowercase.
        """
        if not word:
            return np.zeros(BINS, dtype=complex)

        if word in self._wave_cache:
            return self._wave_cache[word]

        k = np.arange(BINS, dtype=float)
        wave = np.zeros(BINS, dtype=complex)

        max_freq = max(1, BINS // 4 - 1)

        for i, ch in enumerate(word):
            code = ord(ch)
            freq = (code % max_freq) + 1
            phase = self._hash_float("phase", word, i, code) * 2.0 * math.pi

            wave += np.exp(
                1j * ((2.0 * math.pi * freq * k / float(BINS)) + phase)
            )

        wave /= float(len(word))
        wave = self._normalize(wave)

        self._wave_cache[word] = wave
        return wave

    def _text_spectrum(self, tokens):
        if not tokens:
            return np.zeros(BINS, dtype=complex)

        used = tokens[:BINS]
        n = len(used)

        wave = np.zeros(BINS, dtype=complex)

        for idx, token in enumerate(used):
            token_wave = self._word_wave(token)
            pos_phase = np.exp(1j * 2.0 * math.pi * idx / float(n))
            wave += token_wave * pos_phase

        wave /= float(n)

        # If the positional wave cancels itself, use plain superposition.
        if np.linalg.norm(wave) < EPS:
            wave = np.zeros(BINS, dtype=complex)
            for token in used:
                wave += self._word_wave(token)
            wave /= float(n)

        return self._normalize(wave)

    # ==================================================================
    # TOPOLOGY
    # ==================================================================

    def _spectrum_to_xyz(self, spectrum):
        spectrum = np.asarray(spectrum, dtype=complex)
        magnitudes = np.abs(spectrum)
        total = np.sum(magnitudes)

        if total < EPS:
            return np.array([0.0, 0.0, 0.0], dtype=float)

        k = np.arange(BINS, dtype=float)

        centroid = float(np.sum(k * magnitudes) / total)
        dominant = float(np.argmax(magnitudes))
        prob = magnitudes / total

        entropy = float(-np.sum(prob * np.log2(prob + EPS)))

        x = centroid / float(BINS)
        y = dominant / float(BINS)
        z = entropy / (math.log2(BINS) + EPS)

        return np.array([x, y, z], dtype=float)

    # ==================================================================
    # IDENTITY
    # ==================================================================

    def _get_vocab_mean_spectrum(self):
        if not self.nodes:
            return np.zeros(BINS, dtype=complex)

        spectra = [data["spectrum"] for data in self.nodes.values()]
        return np.mean(spectra, axis=0)

    def _safe_identity(self, spectrum, vocab_mean):
        identity = self._normalize(np.asarray(spectrum, dtype=complex) - vocab_mean)

        if np.linalg.norm(identity) < EPS:
            identity = self._normalize(spectrum)

        return identity

    # ==================================================================
    # LEARN
    # ==================================================================

    def learn(self, text, save_after=True):
        tokens = self._tokenize(text)

        if not tokens:
            return

        for token in tokens:
            spectrum = self._word_wave(token)
            self._register_node(token, spectrum)

        n = len(tokens)

        if n <= BINS:
            for i in range(n):
                for j in range(i + 1, n):
                    weight = 1.0 / float(j - i)
                    self._update_link(tokens[i], tokens[j], weight)
        else:
            for i in range(n - 1):
                self._update_link(tokens[i], tokens[i + 1], 1.0)

        if save_after:
            self._save()

    def _register_node(self, word, spectrum):
        spectrum = self._normalize(spectrum)

        if np.linalg.norm(spectrum) < EPS:
            return

        if word in self.nodes:
            node = self.nodes[word]

            node["count"] += 1
            node["spectrum_sum"] += spectrum

            node_spectrum = self._normalize(node["spectrum_sum"])

            if np.linalg.norm(node_spectrum) < EPS:
                node_spectrum = self._word_wave(word)

            node["spectrum"] = node_spectrum
            node["xyz"] = self._spectrum_to_xyz(node_spectrum)
            node["phase"] = self._phase_from_spectrum(node_spectrum)
            node["mass"] = 1.0 + math.log1p(node["count"])
            return

        spectrum_sum = spectrum.copy()
        node_spectrum = self._normalize(spectrum_sum)

        if np.linalg.norm(node_spectrum) < EPS:
            node_spectrum = spectrum

        self.nodes[word] = {
            "spectrum_sum": spectrum_sum,
            "spectrum": node_spectrum,
            "xyz": self._spectrum_to_xyz(node_spectrum),
            "phase": self._phase_from_spectrum(node_spectrum),
            "mass": 1.0 + math.log1p(1),
            "count": 1,
        }

    def _update_link(self, w1, w2, weight):
        if weight <= 0.0:
            return

        if w1 not in self.nodes or w2 not in self.nodes:
            return

        key = tuple(sorted((w1, w2)))

        spec1 = self.nodes[w1]["spectrum"]
        spec2 = self.nodes[w2]["spectrum"]

        pair_spectrum = self._normalize(spec1 + spec2)

        if np.linalg.norm(pair_spectrum) < EPS:
            pair_spectrum = self._normalize(spec1 * np.conj(spec2))

        if np.linalg.norm(pair_spectrum) < EPS:
            pair_spectrum = self._normalize(spec1)

        if np.linalg.norm(pair_spectrum) < EPS:
            return

        if key not in self.links:
            self.links[key] = {
                "spectrum_sum": np.zeros(BINS, dtype=complex),
                "spectrum": pair_spectrum.copy(),
                "count": 0.0,
            }

        link = self.links[key]

        link["count"] += float(weight)
        link["spectrum_sum"] += pair_spectrum * float(weight)

        link_spectrum = self._normalize(link["spectrum_sum"])

        if np.linalg.norm(link_spectrum) < EPS:
            link_spectrum = pair_spectrum

        link["spectrum"] = link_spectrum

    # ==================================================================
    # LEARNING MODE: WEAK / REINFORCE / RECTIFY
    # ==================================================================

    def _weaken_link(self, w1, w2, weight=1.0):
        """
        Weakens a relational link between two nodes.
        """
        if w1 not in self.nodes or w2 not in self.nodes:
            return

        key = tuple(sorted((w1, w2)))

        if key not in self.links:
            return

        link = self.links[key]

        spec1 = self.nodes[w1]["spectrum"]
        spec2 = self.nodes[w2]["spectrum"]

        pair_spectrum = self._normalize(spec1 + spec2)

        link["count"] = max(0.0, float(link.get("count", 0.0)) - float(weight))

        if np.linalg.norm(pair_spectrum) > EPS:
            link["spectrum_sum"] -= pair_spectrum * float(weight)

        link_spectrum = self._normalize(link["spectrum_sum"])

        if np.linalg.norm(link_spectrum) < EPS:
            link_spectrum = np.zeros(BINS, dtype=complex)

        link["spectrum"] = link_spectrum

        if link["count"] <= EPS and np.linalg.norm(link["spectrum_sum"]) < EPS:
            self.links.pop(key, None)

    def reinforce_answer(self, input_text, output_text):
        """
        Accepted answer: reinforces input -> answer.
        """
        output_text = output_text.strip()

        if not output_text:
            return

        # The accepted answer also becomes experience.
        self.learn(output_text, save_after=False)

        input_tokens = self._words(input_text)
        output_tokens = self._words(output_text)

        for a in input_tokens:
            for b in output_tokens:
                if a != b:
                    self._update_link(a, b, 1.0)

    def rectify_answer(self, input_text, wrong_text, correction_text):
        """
        Corrected answer:
        - weakens input -> wrong answer
        - reinforces input -> correction
        """
        correction_text = correction_text.strip()

        if not correction_text:
            self.reinforce_answer(input_text, wrong_text)
            return

        # The correction enters as positive experience.
        self.learn(correction_text, save_after=False)

        input_tokens = self._words(input_text)
        wrong_tokens = self._words(wrong_text)
        good_tokens = self._words(correction_text)

        # Reinforce the correct path.
        for a in input_tokens:
            for b in good_tokens:
                if a != b:
                    self._update_link(a, b, 1.0)

        # Weaken the wrong path.
        for a in input_tokens:
            for b in wrong_tokens:
                if a != b:
                    self._weaken_link(a, b, 1.0)

    # ==================================================================
    # GRAPH
    # ==================================================================

    def _build_adjacency(self):
        adjacency = {}

        for (a, b), link in self.links.items():
            count = max(0.0, float(link.get("count", 0.0)))

            if count <= EPS:
                continue

            strength = math.log1p(count)

            adjacency.setdefault(a, []).append((b, strength))
            adjacency.setdefault(b, []).append((a, strength))

        return adjacency

    def _candidate_cascade(self, tokens, node_ids, input_id):
        primary = {}

        for t in tokens:
            if t in self.nodes and t in node_ids:
                primary[t] = 1.0

        if not primary:
            return {}

        adjacency = self._build_adjacency()
        candidates = dict(primary)

        # Secondary candidates.
        secondary = {}

        for p in primary:
            for other, strength in adjacency.get(p, []):
                if other in candidates:
                    continue
                if other not in node_ids:
                    continue

                res = self._spectral_resonance(node_ids[other], node_ids[p])
                val = res * strength

                if val > secondary.get(other, 0.0):
                    secondary[other] = val

        secondary = {
            w: v / (1.0 + v)
            for w, v in secondary.items()
        }

        for w, v in secondary.items():
            if w not in candidates or v > candidates[w]:
                candidates[w] = v

        # Tertiary candidates.
        tertiary = {}

        for s, sval in secondary.items():
            if sval <= EPS:
                continue

            for other, strength in adjacency.get(s, []):
                if other in candidates:
                    continue
                if other not in node_ids:
                    continue

                res = self._spectral_resonance(node_ids[other], node_ids[s])
                val = res * strength * sval

                if val > tertiary.get(other, 0.0):
                    tertiary[other] = val

        tertiary = {
            w: v / (1.0 + v)
            for w, v in tertiary.items()
        }

        for w, v in tertiary.items():
            if w not in candidates or v > candidates[w]:
                candidates[w] = v

        if np.linalg.norm(input_id) < EPS:
            return candidates

        # Interference: it does not remove candidates absolutely.
        filtered = {}

        for w, base in candidates.items():
            interf = self._signed_interference(node_ids[w], input_id)

            if interf > 0.0:
                factor = interf
            else:
                factor = EPS

            filtered[w] = base * factor

        return filtered

    # ==================================================================
    # EXPRESSION
    # ==================================================================

    def express(self, prompt=""):
        if not self.nodes:
            return ""

        tokens = self._tokenize(prompt)

        if not tokens:
            top = max(self.nodes.items(), key=lambda x: x[1]["mass"])
            return top[0]

        vocab_mean = self._get_vocab_mean_spectrum()

        node_ids = {}

        for word, data in self.nodes.items():
            node_ids[word] = self._safe_identity(data["spectrum"], vocab_mean)

        link_ids = {}

        for key, link in self.links.items():
            link_ids[key] = self._safe_identity(link["spectrum"], vocab_mean)

        input_spec = self._text_spectrum(tokens)
        input_id = self._normalize(input_spec - vocab_mean)

        if np.linalg.norm(input_id) < EPS:
            input_id = self._normalize(input_spec)

        candidates = self._candidate_cascade(tokens, node_ids, input_id)

        if not candidates:
            return ""

        best_word = max(candidates, key=candidates.get)

        known = [t for t in tokens if t in candidates]

        if known:
            mean_coupling = float(np.mean([candidates[t] for t in known]))
        else:
            mean_coupling = 0.0

        energy = math.log1p(len(tokens)) * (1.0 + max(0.0, mean_coupling))

        current_word = best_word
        current_data = self.nodes[current_word]

        seed_id = node_ids[current_word]

        if np.linalg.norm(seed_id) < EPS:
            if np.linalg.norm(input_id) > EPS:
                seed_id = input_id.copy()
            else:
                seed_id = current_data["spectrum"].copy()

        trajectory_sum = seed_id.copy()
        trajectory_id = self._normalize(trajectory_sum)

        if np.linalg.norm(trajectory_id) < EPS:
            trajectory_id = current_data["spectrum"].copy()
            trajectory_sum = trajectory_id.copy()

        trajectory_xyz = current_data["xyz"].copy()
        trajectory_phase = current_data["phase"]
        trajectory_count = 1

        result = []
        counts = {}
        max_steps = len(candidates)

        while energy > EPS and len(result) < max_steps:
            result.append(current_word)
            counts[current_word] = counts.get(current_word, 0) + 1

            scores = []
            words = []

            for word in candidates:
                data = self.nodes[word]

                fatigue = float((1 + counts.get(word, 0)) ** 2)
                node_id = node_ids[word]

                input_coupling = candidates[word]
                res_traj = self._spectral_resonance(node_id, trajectory_id)
                amplitude = math.log1p(data["mass"])

                score = input_coupling * res_traj * amplitude

                link_key = tuple(sorted((current_word, word)))

                if link_key in self.links:
                    link = self.links[link_key]
                    link_id = link_ids.get(link_key)

                    if link_id is not None and np.linalg.norm(link_id) > EPS:
                        res_link = self._spectral_resonance(link_id, trajectory_id)
                        link_amp = math.log1p(max(0.0, link.get("count", 0.0)))
                        score *= (1.0 + res_link * link_amp)

                score /= fatigue

                scores.append(score)
                words.append(word)

            if not scores:
                break

            scores = np.array(scores, dtype=float)
            scores = np.where(scores > 0.0, scores, 0.0)

            total_score = np.sum(scores)

            if total_score < EPS:
                break

            probs = scores / (total_score + EPS)
            cum = np.cumsum(probs)

            r = self._hash_float(current_word, len(result), energy, trajectory_count)
            idx = int(np.searchsorted(cum, r))

            if idx >= len(words):
                idx = len(words) - 1

            next_word = words[idx]
            next_data = self.nodes[next_word]

            coherence = self._phase_coherence(trajectory_phase, next_data["phase"])
            jump_dist = float(np.linalg.norm(trajectory_xyz - next_data["xyz"])) + EPS
            penalty = max(EPS, 1.0 - coherence)

            denominator = (
                math.log1p(current_data["mass"])
                + math.log1p(next_data["mass"])
                + EPS
            )

            cost = (jump_dist * penalty) / denominator
            cost = max(cost, 1.0 / (1.0 + len(candidates)))

            energy -= cost

            next_id = node_ids[next_word]

            if np.linalg.norm(next_id) < EPS:
                next_id = next_data["spectrum"].copy()

            trajectory_sum += next_id
            trajectory_id = self._normalize(trajectory_sum)

            if np.linalg.norm(trajectory_id) < EPS:
                trajectory_id = next_id.copy()
                trajectory_sum = next_id.copy()

            trajectory_xyz = (
                trajectory_xyz * trajectory_count + next_data["xyz"]
            ) / (trajectory_count + 1.0)

            if np.linalg.norm(trajectory_sum) > EPS:
                trajectory_phase = self._phase_from_spectrum(trajectory_sum)
            else:
                trajectory_phase = next_data["phase"]

            trajectory_count += 1

            current_word = next_word
            current_data = next_data

        return " ".join(result) if result else ""

    # ==================================================================
    # PERSIST
    # ==================================================================

    def _save(self):
        try:
            cur = self.conn.cursor()

            cur.execute("DELETE FROM nodes")
            cur.execute("DELETE FROM links")

            node_rows = []

            for word, data in self.nodes.items():
                spectrum_sum = data.get("spectrum_sum", data["spectrum"])
                real, imag = self._complex_to_blobs(spectrum_sum)

                node_rows.append(
                    (
                        word,
                        real,
                        imag,
                        int(data.get("count", 1)),
                    )
                )

            cur.executemany(
                "INSERT INTO nodes(word, real, imag, count) VALUES(?, ?, ?, ?)",
                node_rows
            )

            link_rows = []

            for (w1, w2), data in self.links.items():
                spectrum_sum = data.get("spectrum_sum", data["spectrum"])
                real, imag = self._complex_to_blobs(spectrum_sum)

                link_rows.append(
                    (
                        w1,
                        w2,
                        real,
                        imag,
                        float(data.get("count", 0.0)),
                    )
                )

            cur.executemany(
                "INSERT INTO links(w1, w2, real, imag, count) VALUES(?, ?, ?, ?, ?)",
                link_rows
            )

            self.conn.commit()

        except Exception:
            try:
                self.conn.rollback()
            except Exception:
                pass

    def _load(self):
        self.nodes = {}
        self.links = {}

        try:
            cur = self.conn.cursor()

            cur.execute("SELECT word, real, imag, count FROM nodes")

            for word, real_blob, imag_blob, count in cur.fetchall():
                spectrum_sum = self._blob_to_complex(real_blob, imag_blob)

                if spectrum_sum is None:
                    continue

                spectrum = self._normalize(spectrum_sum)

                if np.linalg.norm(spectrum) < EPS:
                    spectrum = self._word_wave(word)

                count = int(count)

                self.nodes[word] = {
                    "spectrum_sum": spectrum_sum,
                    "spectrum": spectrum,
                    "xyz": self._spectrum_to_xyz(spectrum),
                    "phase": self._phase_from_spectrum(spectrum),
                    "mass": 1.0 + math.log1p(count),
                    "count": count,
                }

            cur.execute("SELECT w1, w2, real, imag, count FROM links")

            for w1, w2, real_blob, imag_blob, count in cur.fetchall():
                spectrum_sum = self._blob_to_complex(real_blob, imag_blob)

                if spectrum_sum is None:
                    continue

                spectrum = self._normalize(spectrum_sum)

                self.links[(w1, w2)] = {
                    "spectrum_sum": spectrum_sum,
                    "spectrum": spectrum,
                    "count": float(count),
                }

        except Exception:
            self.nodes = {}
            self.links = {}


# ======================================================================
# CORPUS
# ======================================================================

def _extract_text(path):
    suffix = path.suffix

    if suffix in (".txt", ".TXT"):
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return None

    if suffix in (".pdf", ".PDF"):
        try:
            import fitz
        except ImportError:
            return None

        try:
            doc = fitz.open(str(path))
            pages = []

            for page in doc:
                pages.append(page.get_text())

            doc.close()
            return " ".join(pages)

        except Exception:
            return None

    return ""


def ingest_corpus(core):
    if not CORPUS_DIR.exists():
        return

    try:
        cur = core.conn.cursor()
        cur.execute("SELECT file_id FROM corpus_files")
        known = {row[0] for row in cur.fetchall()}
    except Exception:
        known = set()

    files = sorted([
        p for p in CORPUS_DIR.rglob("*")
        if p.is_file() and p.suffix in (".txt", ".TXT", ".pdf", ".PDF")
    ])

    if not files:
        print("Lakota > corpus folder is empty.")
        return

    ingested_any = False
    missing_fitz = False

    for path in files:
        try:
            st = path.stat()
            file_id = f"{path.relative_to(CORPUS_DIR)}|{st.st_size}|{st.st_mtime}"
        except OSError as e:
            print(f"Lakota > could not read {path.name}: {e}")
            continue

        if file_id in known:
            continue

        text = _extract_text(path)

        if text is None:
            if path.suffix in (".pdf", ".PDF"):
                missing_fitz = True
            else:
                print(f"Lakota > could not extract text from {path.name}")
            continue

        if text.strip():
            core.learn(text, save_after=False)

        core._mark_file(file_id)

        ingested_any = True
        core._save()

        print(f"Lakota > corpus ingested: {path.name}")

    if missing_fitz:
        print("Lakota > to ingest PDF files install PyMuPDF:")
        print("          pip install PyMuPDF")

    if ingested_any:
        core._save()


# ======================================================================
# MAIN
# ======================================================================

def main():
    core = Lakota()

    print(" L A K O T A ")
    print("1/ Normal mode")
    print("2/ Learning mode")

    try:
        mode = input("Mode > ").strip()
    except EOFError:
        mode = "1"

    learning_mode = mode.startswith("2")

    print("Ctrl+C to exit.\n")

    ingest_corpus(core)

    if learning_mode:
        print("\n--- Lakota learn mode ---")
    else:
        print("\n--- Lakota hear ---")

    try:
        while True:
            try:
                user_in = input("You > ")
            except EOFError:
                break

            if not user_in.strip():
                continue

            # Lakota learns while listening.
            core.learn(user_in)

            # Lakota answers.
            out = core.express(user_in)

            if out:
                print(f"Lakota > {out}")
            else:
                print("Lakota >")

            # Learning mode: human correction.
            if learning_mode:
                try:
                    correction = input("Correction (Enter if ok) > ")
                except EOFError:
                    correction = ""

                if correction.strip():
                    core.rectify_answer(user_in, out, correction)
                    print("Lakota > correction integrated")
                else:
                    core.reinforce_answer(user_in, out)
                    print("Lakota > answer accepted")

            core._save()

    except KeyboardInterrupt:
        pass

    finally:
        core.close()


if __name__ == "__main__":
    main()
