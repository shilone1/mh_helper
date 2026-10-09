"""Offline coating checks; no real screenshots or mouse input."""

import unittest
from unittest.mock import patch

import cv2
import numpy as np

from lottery_completion import coating_is_cleared, make_completion_check


class LotteryCompletionTests(unittest.TestCase):
    def setUp(self):
        self.cleared = np.full((68, 212, 3), (90, 190, 240), dtype=np.uint8)
        for x in (20, 85, 150):
            self.cleared[18:48, x:x + 28] = (40, 160, 40)

    def test_revealed_gold_and_rewards(self):
        self.assertTrue(coating_is_cleared(self.cleared))

    def test_original_coating(self):
        from app_paths import resource_path
        image = cv2.imread(resource_path('img_templates', 'menghuan_lottery.png'))
        self.assertIsNotNone(image)
        self.assertFalse(coating_is_cleared(image))

    def test_remaining_stripe_or_patch(self):
        for region in ((slice(30, 33), slice(4, 208)),
                       (slice(25, 30), slice(80, 85)),
                       (slice(4, 64), slice(140, 208))):
            image = self.cleared.copy()
            image[region] = 165
            self.assertFalse(coating_is_cleared(image))

    def test_missing_panel_background_is_not_completion(self):
        for value in (0, 255):
            self.assertFalse(coating_is_cleared(np.full_like(self.cleared, value)))
        self.assertFalse(coating_is_cleared(None))

    def test_two_frames_and_panel_anchor_required(self):
        from app_paths import resource_path
        path = resource_path('img_templates', 'lottery_close.png')
        template = cv2.imread(path)
        h, w = template.shape[:2]
        frame = np.zeros((200, 400, 3), dtype=np.uint8)
        frame[5:5 + h, 5:5 + w] = template
        frame[100:168, 100:312] = self.cleared
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        covered = frame.copy()
        covered[100:168, 100:312] = 165
        covered_rgb = cv2.cvtColor(covered, cv2.COLOR_BGR2RGB)
        with patch('pyautogui.screenshot', return_value=rgb) as capture, \
                patch('lottery_completion.time.sleep'):
            check = make_completion_check((100, 100, 312, 168), (0, 0, 400, 200), path)
            self.assertTrue(check())
            capture.side_effect = [rgb, covered_rgb]
            self.assertFalse(check())
            capture.side_effect = None
            missing_panel = frame.copy()
            missing_panel[5:5 + h, 5:5 + w] = 0
            capture.return_value = cv2.cvtColor(missing_panel, cv2.COLOR_BGR2RGB)
            self.assertFalse(check())


if __name__ == '__main__':
    unittest.main()
