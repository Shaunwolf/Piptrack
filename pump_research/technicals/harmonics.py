"""
Harmonic (XABCD) patterns found on zigzag pivots.

Ratios follow the common Carney/Pesavento definitions with a small tolerance:
  ab_xa = |AB|/|XA|, bc_ab = |BC|/|AB|, cd_bc = |CD|/|BC|, ad_xa = |AD|/|XA|
A pattern is bullish when D is a swing low (the expected reversal is up).
"""

from typing import List

from .pivots import Pivot

TOL = 0.04

# name: (ab_xa, bc_ab, cd_bc, ad_xa) ranges
XABCD_PATTERNS = {
    "gartley":    ((0.618, 0.618), (0.382, 0.886), (1.13, 1.618), (0.786, 0.786)),
    "bat":        ((0.382, 0.50), (0.382, 0.886), (1.618, 2.618), (0.886, 0.886)),
    "alt_bat":    ((0.382, 0.382), (0.382, 0.886), (2.0, 3.618), (1.13, 1.13)),
    "butterfly":  ((0.786, 0.786), (0.382, 0.886), (1.618, 2.24), (1.27, 1.618)),
    "crab":       ((0.382, 0.618), (0.382, 0.886), (2.24, 3.618), (1.618, 1.618)),
    "deep_crab":  ((0.886, 0.886), (0.382, 0.886), (2.0, 3.618), (1.618, 1.618)),
    "shark":      ((0.446, 0.618), (1.13, 1.618), (1.618, 2.24), (0.886, 1.13)),
}


def _in(value, rng, tol=TOL):
    lo, hi = rng
    return lo * (1 - tol) - tol / 2 <= value <= hi * (1 + tol) + tol / 2


def _closeness(value, rng):
    """1.0 at the centre of the range, falling off with relative distance"""
    centre = (rng[0] + rng[1]) / 2
    return max(0.0, 1 - abs(value - centre) / max(centre, 1e-9))


def _leg(a: Pivot, b: Pivot):
    return abs(b.price - a.price)


def _pattern(name, pts, ratios, ranges):
    score = sum(_closeness(r, rg) for r, rg in zip(ratios.values(), ranges)) / len(ranges)
    return {
        "type": "harmonic",
        "name": name,
        "direction": "bullish" if pts[-1].kind == "low" else "bearish",
        "completed_idx": pts[-1].idx,
        "points": [{"label": lbl, "idx": p.idx, "price": p.price}
                   for lbl, p in zip("XABCD"[-len(pts):], pts)],
        "ratios": {k: round(v, 3) for k, v in ratios.items()},
        "score": round(score, 3),
        "confirmed": pts[-1].confirmed,
    }


def find_harmonics(pivots: List[Pivot], tol: float = TOL) -> List[dict]:
    """Completed patterns. `tol` widens or narrows every ratio window (0.04 = 4%)."""
    def _in(value, rng, tol=tol):
        lo, hi = rng
        return lo * (1 - tol) - tol / 2 <= value <= hi * (1 + tol) + tol / 2

    found = []
    for i in range(len(pivots) - 4):
        x, a, b, c, d = pivots[i:i + 5]
        xa, ab, bc, cd = _leg(x, a), _leg(a, b), _leg(b, c), _leg(c, d)
        if min(xa, ab, bc, cd) <= 0:
            continue
        ratios = {"ab_xa": ab / xa, "bc_ab": bc / ab, "cd_bc": cd / bc, "ad_xa": abs(d.price - a.price) / xa}
        for name, ranges in XABCD_PATTERNS.items():
            if all(_in(r, rg) for r, rg in zip(ratios.values(), ranges)):
                found.append(_pattern(name, (x, a, b, c, d), ratios, ranges))

        # Cypher: C extends beyond A (1.272-1.414 of XA), D retraces 0.786 of XC
        xc = abs(c.price - x.price)
        if xc > 0:
            cy = {"ab_xa": ab / xa, "xc_xa": xc / xa, "cd_xc": cd / xc}
            cy_ranges = ((0.382, 0.618), (1.272, 1.414), (0.786, 0.786))
            beyond_a = (c.price > a.price) if a.kind == "high" else (c.price < a.price)
            if beyond_a and all(_in(r, rg) for r, rg in zip(cy.values(), cy_ranges)):
                found.append(_pattern("cypher", (x, a, b, c, d), cy, cy_ranges))

        # 5-0: B extends beyond X (1.13-1.618 of XA), C extends 1.618-2.24 of AB, D retraces 50% of BC
        five0 = {"ab_xa": ab / xa, "bc_ab": bc / ab, "cd_bc": cd / bc}
        five0_ranges = ((1.13, 1.618), (1.618, 2.24), (0.5, 0.5))
        if all(_in(r, rg) for r, rg in zip(five0.values(), five0_ranges)):
            found.append(_pattern("five_zero", (x, a, b, c, d), five0, five0_ranges))

    # AB=CD on four pivots
    for i in range(len(pivots) - 3):
        a, b, c, d = pivots[i:i + 4]
        ab, bc, cd = _leg(a, b), _leg(b, c), _leg(c, d)
        if min(ab, bc) <= 0:
            continue
        r = {"bc_ab": bc / ab, "cd_bc": cd / bc, "cd_ab": cd / ab}
        rg = ((0.382, 0.886), (1.13, 2.618), (0.9, 1.1))
        if all(_in(v, g) for v, g in zip(r.values(), rg)):
            found.append(_pattern("abcd", (a, b, c, d), r, rg))
    return found


# How far the D leg runs for each pattern, used to project the reversal zone of a pattern still forming:
# name: (ab_xa, bc_ab, D as a retracement of XA, D as a multiple of BC)
PROJECTIONS = {name: (r[0], r[1], r[3], r[2]) for name, r in XABCD_PATTERNS.items()}


def projected_harmonics(pivots: List[Pivot], close: float, tol: float = TOL) -> List[dict]:
    """
    Patterns still forming: X, A, B and C are in place and price is travelling the C→D leg.
    Returns each pattern's potential reversal zone (PRZ): where its XA retracement and BC
    projection for D overlap, and how far the latest close is from it.
    """
    def _in(value, rng):
        lo, hi = rng
        return lo * (1 - tol) - tol / 2 <= value <= hi * (1 + tol) + tol / 2

    candidates = []
    if len(pivots) >= 4:
        candidates.append(pivots[-4:])                      # C is the latest swing
    if len(pivots) >= 5 and not pivots[-1].confirmed:
        candidates.append(pivots[-5:-1])                    # the last pivot is the D leg in progress
    found = []
    for x, a, b, c in candidates:
        xa, ab, bc = _leg(x, a), _leg(a, b), _leg(b, c)
        if min(xa, ab, bc) <= 0:
            continue
        s = 1 if a.price > x.price else -1                  # +1: D forms below (bullish reversal)
        zones = {}
        for name, (ab_rg, bc_rg, ad_rg, cd_rg) in PROJECTIONS.items():
            if not (_in(ab / xa, ab_rg) and _in(bc / ab, bc_rg)):
                continue
            from_xa = sorted(a.price - s * r * xa for r in ad_rg)
            from_bc = sorted(c.price - s * k * bc for k in cd_rg)
            lo, hi = max(from_xa[0], from_bc[0]), min(from_xa[1], from_bc[1])
            overlap = lo <= hi
            if not overlap:                                  # no overlap: the zone spans the gap between them
                lo, hi = min(from_xa[1], from_bc[1]), max(from_xa[0], from_bc[0])
            zones[name] = (lo, hi, overlap, (ab / xa, bc / ab))
        xc = abs(c.price - x.price)
        beyond_a = (c.price > a.price) if s == 1 else (c.price < a.price)
        if xc > 0 and beyond_a and _in(ab / xa, (0.382, 0.618)) and _in(xc / xa, (1.272, 1.414)):
            d = c.price - s * 0.786 * xc
            zones["cypher"] = (d * (1 - tol / 2), d * (1 + tol / 2), True, (ab / xa, xc / xa))
        if _in(bc / ab, (0.382, 0.886)):
            lo, hi = sorted(c.price - s * k * ab for k in (0.9, 1.1))
            zones["abcd"] = (lo, hi, True, (bc / ab,))
        pad = tol / 2 * xa                                   # the PRZ is a band, not a single price
        for name, (lo, hi, overlap, ratios) in zones.items():
            lo, hi = lo - pad, hi + pad
            if lo <= 0:
                continue
            mid = (lo + hi) / 2
            if lo <= close <= hi:
                distance, status = 0.0, "in_zone"
            elif (s == 1 and close > hi) or (s == -1 and close < lo):
                distance, status = abs(close - (hi if s == 1 else lo)) / close, "approaching"
            else:
                distance, status = abs(close - (lo if s == 1 else hi)) / close, "overshot"
            moving_toward = (close < c.price) if s == 1 else (close > c.price)
            found.append({
                "type": "harmonic", "name": name, "direction": "bullish" if s == 1 else "bearish",
                "status": status, "prz_low": lo, "prz_high": hi, "prz_mid": mid, "zones_overlap": overlap,
                "distance": distance, "leg_started": moving_toward, "completed_idx": c.idx,
                "points": [{"label": lbl, "idx": p.idx, "price": p.price} for lbl, p in zip("XABC", (x, a, b, c))],
                "ratios": [round(r, 3) for r in ratios],
            })
    return found
