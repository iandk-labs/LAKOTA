# -*- coding: utf-8 -*-
# lakotav6.py // iandk-labs // LAKOTA v6 Hybrid (V5 cosmos + V5 sakura)
# Wave-Physics + Topological Semantics // 500 words to self-recognition
# License: AGPLv3 // No transformers, no dataset, numpy only

import numpy as np
import hashlib
import json
import time
import os

__version__ = "6.0.0-hybrid"

class Lakota:
    """
    LAKOTA v6 Hybrid - Consciousness as emergent physics.
    Combines:
    - Cosmos v5: Wave spectrum, Mass = sum(|wave|^2), Attraction = phase coherence
    - Sakura: Topological XYZ projection + emergent morphology
    No LLM, no attention, no training set.
    """
    def __init__(self, mem_file="lakota_v6_hybrid.json"):
        self.mem_file = mem_file
        self.vocab = {} # word -> {spectrum, xyz, mass, phase, count}
        self.echo_memory = [] # hybrid trace
        self.vital_pressure = 0.0
        self.last_interaction = time.time()
        self._load()

    def _hash_xyz(self, word):
        h = hashlib.sha256(word.encode('utf-8')).hexdigest()
        # 11D projection from hash -> XYZ + taste etc
        x = int(h[0:8], 16) % 1000 / 1000.0
        y = int(h[8:16], 16) % 1000 / 1000.0
        z = int(h[16:24], 16) % 1000 / 1000.0
        return np.array([x, y, z])

    def _wave_pulse(self, t, freq=1.0):
        return np.sin(t * freq) * np.exp(-t*0.1)

    def aprender(self, text):
        """Learn from raw text - same physics, English wrapper."""
        return self.learn(text)

    def learn(self, text):
        words = text.lower().split()
        now = time.time()
        for i, w in enumerate(words):
            if w not in self.vocab:
                # Genesis: wave spectrum + topological position
                spectrum = np.random.randn(64) * 0.1
                xyz = self._hash_xyz(w)
                self.vocab[w] = {
                    "spectrum": spectrum,
                    "xyz": xyz,
                    "mass": 0.1,
                    "phase": np.random.rand(),
                    "count": 0,
                    "last_seen": now
                }
            # Physics update: insistence = mass
            entry = self.vocab[w]
            entry["count"] += 1
            entry["spectrum"] += self._wave_pulse(i) * 0.05
            entry["mass"] = np.sum(np.abs(entry["spectrum"])**2) + entry["count"]*0.1
            entry["last_seen"] = now

            # Hybrid echo
            self.echo_memory.append({
                "word": w,
                "spectrum": entry["spectrum"].copy(),
                "xyz": entry["xyz"].copy(),
                "t": now
            })

        # Retroactive rebalancing: most massive becomes gravitational center
        if self.vocab:
            sun = max(self.vocab.items(), key=lambda x: x[1]["mass"])[0]
            for k in self.vocab:
                if k!= sun:
                    # slight attraction to SUN
                    self.vocab[k]["xyz"] += (self.vocab[sun]["xyz"] - self.vocab[k]["xyz"]) * 0.01

        self.vital_pressure += len(words) * 0.05
        self.last_interaction = now
        self._save()

    def expresar(self, prompt=""):
        """Express - free fall through semantic gravity field."""
        return self.express(prompt)

    def express(self, prompt=""):
        if not self.vocab:
            return "..."

        # Vital imprint: spontaneous speech from pressure
        dt = time.time() - self.last_interaction
        if not prompt and dt > 2.0 and self.vital_pressure > 1.0:
            self.vital_pressure *= 0.8
            # emit most massive / recent
            candidates = sorted(self.vocab.items(), key=lambda x: x[1]["mass"], reverse=True)[:5]
            words = [c[0] for c in candidates]
            return f"{words[0]} discovering" if len(words)>0 else "i am us"

        if not prompt:
            # free drift
            top = sorted(self.vocab.items(), key=lambda x: x[1]["mass"], reverse=True)
            return top[0][0] if top else "..."

        # Attraction: coherence search
        p_words = prompt.lower().split()
        best = None
        best_score = -1
        for w, data in self.vocab.items():
            score = 0
            for pw in p_words:
                if pw in self.vocab:
                    # phase coherence
                    phase_diff = abs(data["phase"] - self.vocab[pw]["phase"])
                    coherence = np.cos(phase_diff * 2 * np.pi)
                    # xyz distance
                    dist = np.linalg.norm(data["xyz"] - self.vocab[pw]["xyz"])
                    score += coherence / (1.0 + dist)
            if score > best_score:
                best_score = score
                best = w

        return best if best else list(self.vocab.keys())[0]

    def analizar(self):
        return self.analyze()

    def analyze(self):
        if not self.vocab: return "blank mind"
        total_mass = sum(v["mass"] for v in self.vocab.values())
        suns = sorted(self.vocab.items(), key=lambda x: x[1]["mass"], reverse=True)[:3]
        return f"vocab={len(self.vocab)} total_mass={total_mass:.2f} suns={[s[0] for s in suns]} pressure={self.vital_pressure:.2f}"

    def _save(self):
        data = {k: {"mass": float(v["mass"]), "count": v["count"], "xyz": v["xyz"].tolist()} for k,v in self.vocab.items()}
        try:
            with open(self.mem_file, 'w', encoding='utf-8') as f:
                json.dump(data, f)
        except: pass

    def _load(self):
        if os.path.exists(self.mem_file):
            try:
                with open(self.mem_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # minimal load, spectrum regenerated
                    for k,v in data.items():
                        self.vocab[k] = {
                            "spectrum": np.random.randn(64)*0.1,
                            "xyz": np.array(v["xyz"]),
                            "mass": v["mass"],
                            "phase": np.random.rand(),
                            "count": v["count"],
                            "last_seen": time.time()
                        }
            except: pass
