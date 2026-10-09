"""Offline image evidence and bounded polling for marketplace listing results."""

import time
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np

from app_paths import resource_path
from baitan_pricing import analyze_baitan_pricing
from slot_detection import find_baitan_slots


@lru_cache(maxsize=16)
def template(path):
    result = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
    if result is None:
        raise ValueError(f"Cannot read template: {path}")
    return result


def best_match(image, path):
    icon = template(str(path))
    if image.shape[0] < icon.shape[0] or image.shape[1] < icon.shape[1]:
        return 0.0, (0, 0)
    _, score, _, position = cv2.minMaxLoc(cv2.matchTemplate(image, icon, cv2.TM_CCOEFF_NORMED))
    return float(score), position


def inventory_region(image):
    # The market's right-side item grid, excluding buttons and background animation.
    h, w = image.shape[:2]
    return image[int(h * .29):int(h * .80), int(w * .59):int(w * .91)]


def sell_template_paths():
    return sorted(p for p in Path(resource_path(
        "img_templates", "temporary_glyph_sell")).iterdir()
        if p.is_file() and p.suffix.lower() == ".png")


def glyph_count(image):
    """Count distinct visible items across every configured sell template."""
    region = inventory_region(image)
    candidates = []
    for path in sell_template_paths():
        icon = template(str(path))
        th, tw = icon.shape[:2]
        if th > region.shape[0] or tw > region.shape[1]:
            continue
        scores = cv2.matchTemplate(region, icon, cv2.TM_CCOEFF_NORMED)
        while True:
            _, score, _, (x, y) = cv2.minMaxLoc(scores)
            if score <= .80:
                break
            candidates.append((score, x, y, tw, th))
            scores[max(0, y-th//2):y+th//2+1, max(0, x-tw//2):x+tw//2+1] = -1
    selected = []
    # Suppress across templates too: similar icons and alternate crops may
    # both match the same inventory item. Keep the strongest match once.
    for _, x, y, w, h in sorted(candidates, reverse=True):
        duplicate = False
        for sx, sy, sw, sh in selected:
            overlap = max(0, min(x+w, sx+sw)-max(x, sx)) * max(0, min(y+h, sy+sh)-max(y, sy))
            if overlap / min(w*h, sw*sh) > .5:
                duplicate = True
                break
        if not duplicate:
            selected.append((x, y, w, h))
    return len(selected)


def market_visible(image):
    tab, _ = best_match(image, resource_path("img_templates", "want_to_chushou.png"))
    launch, _ = best_match(image, resource_path("img_templates", "market_launch.png"))
    return tab > .80 and launch <= .80


def observation(before, after, filename, previous_count):
    visible = market_visible(after)
    count = len(find_baitan_slots(after)) if visible else None
    before_glyphs = glyph_count(before)
    after_glyphs = glyph_count(after) if visible else None
    a, b = inventory_region(before), inventory_region(after)
    change = float(np.mean(np.max(cv2.absdiff(a, b), axis=2) > 20))
    evidence = dict(visible=visible, occupied=count, before_glyphs=before_glyphs,
                    after_glyphs=after_glyphs, inventory_changed_fraction=change,
                    glyph_count_scope="all_sell_templates", selected_template=filename)
    if not visible:
        return "ambiguous", evidence
    if count > previous_count:
        return "listed", evidence
    # Do not use a raw count drop as proof: occlusion can hide several icons.
    # Require exactly one fewer icon and a bounded inventory change; broad
    # occlusion/rearrangement is ambiguous rather than evidence of a sale.
    if before_glyphs > 0 and after_glyphs == before_glyphs - 1 and .005 < change < .15:
        return "inventory_decreased", evidence
    # Even a small changed quantity label must prevent an automatic retry.
    if count == previous_count and before_glyphs == after_glyphs and change < .0001:
        return "unchanged", evidence
    return "ambiguous", evidence


def poll_listing(before, filename, previous_count, capture, timeout=5.0,
                 clock=time.monotonic, sleep=time.sleep):
    deadline = clock() + timeout
    history = []
    last_key = None
    stable = 0
    while True:
        after = capture()
        state, evidence = observation(before, after, filename, previous_count)
        history.append(dict(state=state, **evidence))
        key = (state, evidence["occupied"], evidence["after_glyphs"])
        stable = stable + 1 if key == last_key else 1
        last_key = key
        if state in ("listed", "inventory_decreased") and stable >= 2:
            return state, after, history
        if clock() >= deadline:
            return ("unchanged" if state == "unchanged" and stable >= 2 else "ambiguous"), after, history
        sleep(.5)


def recover_pricing(image, ocr, original):
    """Keep the confidence floor; require agreement from two reliable variants."""
    readings = [original]
    for scale, contrast in ((3, False), (6, True), (5, False)):
        readings.append(analyze_baitan_pricing(image, ocr=ocr, ocr_scale=scale,
                                               ocr_contrast=contrast))
    reliable = [r for r in readings if r["target_reliable"]
                and r["reference_price"] is not None and r["reference_price"] > 0
                and r["current_price"] is not None and r["current_price"] > 0
                and r["level"] is not None]
    keys = [(r["level"], r["current_price"], r["reference_price"]) for r in reliable]
    # Disagreement among reliable readings is never settled by majority vote.
    accepted = reliable[-1] if len(keys) >= 2 and len(set(keys)) == 1 else original
    return dict(accepted, recovery_readings=readings,
                recovery_accepted=len(keys) >= 2 and len(set(keys)) == 1)


def template_scores(image):
    region = image[:, image.shape[1]//2:]
    return {p.name: best_match(region, p)[0] for p in
            sell_template_paths()}
