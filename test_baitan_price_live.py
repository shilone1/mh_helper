"""Live price-only check on window 0: python test_baitan_price_live.py.

Requires the sale dialog to be open. Adjusts +/- but never launches a sale.
"""

import json
from pathlib import Path

import cv2
import numpy as np
import pyautogui

from baitan_pricing import _make_ocr, analyze_baitan_pricing
from config import window_capture_areas_
from huoli_utilize import set_market_price


def main():
    window = window_capture_areas_[0]
    ocr = _make_ocr()

    def capture(name):
        screenshot = pyautogui.screenshot(region=window)
        screenshot.save(name)
        return analyze_baitan_pricing(
            cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR), ocr=ocr
        )

    before = capture("pricing_test_before.png")
    print("Before:", json.dumps(before, ensure_ascii=True), flush=True)
    assert before["reference_price"] is not None, "No reliable top reference"
    adjusted = set_market_price(window, ocr)
    after = capture("pricing_test_after.png")
    Path("pricing_test_result.json").write_text(
        json.dumps({"before": before, "after": after, "adjusted": adjusted},
                   ensure_ascii=False, indent=2), encoding="utf-8"
    )
    assert adjusted, "Price adjustment failed"
    assert after["target_reliable"], "Final price is unreliable"
    assert after["reference_price"] == before["reference_price"]
    assert after["current_price"] <= before["reference_price"]
    print(f"PASS: {before['current_price']} -> {after['current_price']}; "
          f"top reference {after['reference_price']}. No sale launched.")


if __name__ == "__main__":
    main()
