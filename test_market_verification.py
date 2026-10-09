"""Offline regression tests. No screenshots or mouse input are sent to the game."""
import unittest
from unittest.mock import patch
from pathlib import Path
from tempfile import TemporaryDirectory

import cv2
import numpy as np

import market_verification as verification


def reading(price=144, reliable=True, confidence=.9):
    return dict(level=60, current_price=price, reference_price=144 if reliable else None,
                target_reliable=reliable, target_price_confidence=confidence,
                target_level_confidence=.99)


class InventoryCountTests(unittest.TestCase):
    def test_variable_template_and_item_counts_with_duplicate_templates(self):
        rng = np.random.default_rng(42)
        with TemporaryDirectory() as folder, patch.object(
                verification, 'resource_path', return_value=folder):
            icons = [rng.integers(0, 256, (32, 32, 3), dtype=np.uint8) for _ in range(8)]
            for template_count in (1, 3, 8):
                for i in range(template_count):
                    cv2.imwrite(str(Path(folder) / f'{i}.PNG'), icons[i])
                # An alternate crop also matches item zero; it must not add an item.
                cv2.imwrite(str(Path(folder) / 'duplicate.png'), icons[0][2:30, 2:30])
                (Path(folder) / 'notes.txt').write_text('ignored')
                for item_count in (0, 1, 4, 9):
                    with self.subTest(templates=template_count, items=item_count):
                        image = np.zeros((505, 638, 3), np.uint8)
                        for i in range(item_count):
                            x, y = 385 + (i % 4)*45, 155 + (i // 4)*50
                            image[y:y+32, x:x+32] = icons[i % template_count]
                        self.assertEqual(verification.glyph_count(image), item_count)
            # Oversized templates are ignored, and an empty folder counts zero.
            cv2.imwrite(str(Path(folder) / 'large.png'), np.zeros((600, 600, 3), np.uint8))
            self.assertEqual(verification.glyph_count(image), 9)
            for path in Path(folder).glob('*'):
                path.unlink()
            self.assertEqual(verification.glyph_count(image), 0)
        verification.template.cache_clear()

    def test_mixed_inventory_drop_is_confirmed_with_real_matching(self):
        rng = np.random.default_rng(43)
        with TemporaryDirectory() as folder, patch.object(
                verification, 'resource_path', return_value=folder):
            before = np.zeros((505, 638, 3), np.uint8)
            for i in range(3):
                icon = rng.integers(0, 256, (32, 32, 3), dtype=np.uint8)
                cv2.imwrite(str(Path(folder) / f'{i}.png'), icon)
                x = 385 + i*45
                before[155:187, x:x+32] = icon
            after = before.copy()
            after[155:187, 430:462] = 0
            with patch.object(verification, 'market_visible', return_value=True), \
                    patch.object(verification, 'find_baitan_slots', return_value=[(1, 2, 3, 4)]):
                state, evidence = verification.observation(before, after, '1.png', 1)
            self.assertEqual(state, 'inventory_decreased')
            self.assertEqual((evidence['before_glyphs'], evidence['after_glyphs']), (3, 2))
        verification.template.cache_clear()


class VerificationTests(unittest.TestCase):
    def poll(self, states):
        now = [0.0]
        def sleep(seconds):
            now[0] += seconds
        samples = [(s, dict(occupied=n, after_glyphs=g)) for s, n, g in states]
        last = samples[-1]
        def observe(*args):
            return samples.pop(0) if samples else last
        with patch.object(verification, 'observation', side_effect=observe):
            result = verification.poll_listing(None, '01.PNG', 1, lambda: None,
                                               clock=lambda: now[0], sleep=sleep)
        return result, now[0]

    def test_delayed_listing_waits_for_two_stable_frames(self):
        result, elapsed = self.poll([('ambiguous', None, None), ('unchanged', 1, 5),
                                     ('listed', 2, 4), ('listed', 2, 4)])
        self.assertEqual(result[0], 'listed')
        self.assertEqual(elapsed, 1.5)

    def test_unchanged_waits_full_five_seconds(self):
        result, elapsed = self.poll([('unchanged', 1, 5)])
        self.assertEqual(result[0], 'unchanged')
        self.assertEqual(elapsed, 5.0)

    def test_one_success_frame_does_not_confirm(self):
        result, _ = self.poll([('listed', 2, 4), ('ambiguous', None, None)])
        self.assertEqual(result[0], 'ambiguous')

    def test_same_count_with_inventory_decrease_can_confirm(self):
        result, _ = self.poll([('inventory_decreased', 1, 4)])
        self.assertEqual(result[0], 'inventory_decreased')

    def test_obscured_dialog_never_proves_success(self):
        image = np.zeros((505, 638, 3), np.uint8)
        with patch.object(verification, 'market_visible', return_value=False), \
                patch.object(verification, 'glyph_count', return_value=5):
            state, evidence = verification.observation(image, image, '01.PNG', 1)
        self.assertEqual(state, 'ambiguous')
        self.assertIsNone(evidence['occupied'])

    def test_inventory_disappearance_with_unchanged_count(self):
        before = np.zeros((505, 638, 3), np.uint8)
        after = before.copy()
        after[200:240, 400:440] = 255
        with patch.object(verification, 'market_visible', return_value=True), \
                patch.object(verification, 'glyph_count', side_effect=[5, 4]), \
                patch.object(verification, 'find_baitan_slots', return_value=[(1, 2, 3, 4)]):
            state, _ = verification.observation(before, after, '01.PNG', 1)
        self.assertEqual(state, 'inventory_decreased')

    def test_small_quantity_change_is_not_safe_to_retry(self):
        before = np.zeros((505, 638, 3), np.uint8)
        after = before.copy()
        after[225:230, 430:435] = 255
        with patch.object(verification, 'market_visible', return_value=True), \
                patch.object(verification, 'glyph_count', side_effect=[5, 5]), \
                patch.object(verification, 'find_baitan_slots', return_value=[(1, 2, 3, 4)]):
            state, _ = verification.observation(before, after, '01.PNG', 1)
        self.assertEqual(state, 'ambiguous')

    def test_ocr_recovery_requires_agreeing_reliable_variants(self):
        original = reading(reliable=False, confidence=.6849)
        with patch.object(verification, 'analyze_baitan_pricing', side_effect=[reading(), reading(), original]):
            result = verification.recover_pricing(None, None, original)
        self.assertTrue(result['recovery_accepted'])
        self.assertEqual(result['current_price'], 144)

    def test_ocr_disagreement_and_low_confidence_do_not_pass(self):
        original = reading(reliable=False, confidence=.6849)
        for variants in ([reading(), reading(145), reading()], [original]*3,
                         [reading(), original, original]):
            with self.subTest(variants=variants), \
                    patch.object(verification, 'analyze_baitan_pricing', side_effect=variants):
                result = verification.recover_pricing(None, None, original)
            self.assertFalse(result['recovery_accepted'])
            self.assertFalse(result['target_reliable'])


class EmptyMarketPricingTests(unittest.TestCase):
    def test_empty_market_keeps_price_but_invalid_readings_still_fail(self):
        import huoli_utilize as huoli
        from contextlib import ExitStack
        image = np.zeros((505, 638, 3), np.uint8)
        for listings, reliable, price, expected in (
                ([], True, 250, True),
                ([{"price": None}], True, 250, False),
                ([], False, 250, False),
                ([], True, None, False),
                ([], True, 0, False)):
            with self.subTest(listings=listings, reliable=reliable, price=price), ExitStack() as stack:
                pricing = dict(reading(price=price, reliable=reliable),
                               reference_price=None, listings=listings)
                stack.enter_context(patch.object(huoli.pyautogui, 'screenshot', return_value=image))
                stack.enter_context(patch.object(huoli, 'analyze_baitan_pricing', return_value=pricing))
                stack.enter_context(patch.object(huoli, 'recover_pricing',
                    return_value=dict(pricing, recovery_accepted=False)))
                for name in ('dismiss_market_event_popup', 'clear_market_hover', 'save_market_diagnostic'):
                    stack.enter_context(patch.object(huoli, name))
                stack.enter_context(patch.object(huoli.time, 'sleep'))
                stack.enter_context(patch('builtins.print'))
                click = stack.enter_context(patch.object(huoli, 'random_click_mouse'))
                readings = []
                self.assertEqual(huoli.set_market_price(
                    (0, 0, 638, 505), None, price_cap=180, readings=readings), expected)
                click.assert_not_called()
                self.assertEqual(readings[-1]['current_price'], price)


class SellingRecoveryTests(unittest.TestCase):
    def run_selling(self, outcome, matches=None):
        # Importing defines functions only; every I/O operation used below is mocked.
        import huoli_utilize as huoli
        from contextlib import ExitStack
        image = np.zeros((505, 638, 3), np.uint8)
        with ExitStack() as stack:
            for name, value in dict(_make_ocr=object(), clear_market_hover=None,
                                    capture_market=image, market_visible=True,
                                    confirm_listing_duration=True,
                                    find_baitan_slots=[(1, 2, 3, 4)], set_market_price=True,
                                    find_icon_on_screen=((446, 402, 524, 426), 1.),
                                    save_market_diagnostic=None, template_scores={'01.PNG': .7}).items():
                stack.enter_context(patch.object(huoli, name, return_value=value))
            stack.enter_context(patch.object(huoli.time, 'sleep'))
            stack.enter_context(patch('builtins.print'))
            clicks = stack.enter_context(patch.object(huoli, 'random_click_mouse', return_value=(480, 414)))
            scans = stack.enter_context(patch.object(huoli, 'find_icons_one_per_window',
                return_value=[((434, 305, 475, 346), 1., '01.PNG')] if matches is None else matches))
            polls = stack.enter_context(patch.object(huoli, 'poll_listing',
                return_value=(outcome, image, [{'occupied': 1, 'after_glyphs': 5}])))
            result = huoli.launch_remaining_glyphs([(0, 0, 638, 505)])
        return result[(0, 0, 638, 505)], clicks.call_count, polls.call_count, scans.call_count

    def test_unchanged_retries_only_once(self):
        result, clicks, polls, _ = self.run_selling('unchanged')
        self.assertEqual((clicks, polls), (4, 2))
        self.assertEqual(result['reason'], 'listing_unchanged')

    def test_ambiguous_never_repeats_click(self):
        result, clicks, polls, _ = self.run_selling('ambiguous')
        self.assertEqual((clicks, polls), (2, 1))
        self.assertEqual(result['reason'], 'listing_ambiguous')

    def test_template_miss_retries_without_clicking(self):
        result, clicks, polls, scans = self.run_selling('unchanged', matches=[])
        self.assertEqual((clicks, polls, scans), (0, 0, 3))
        self.assertEqual(result['reason'], 'no_sell_template_match')


class MarketNavigationTests(unittest.TestCase):
    def navigate(self, initial, shop_opens_sell=False):
        import huoli_utilize as huoli
        from contextlib import ExitStack
        state = [initial]
        clicked = []
        names = {"shangcheng.png": (1, 1, 2, 2), "baitan.png": (3, 3, 4, 4),
                 "want_to_chushou.png": (5, 5, 6, 6)}
        visible = {"world": "shangcheng.png", "shop": "baitan.png",
                   "stall": "want_to_chushou.png"}
        def find(path, **kwargs):
            name = Path(path).name
            return (names[name], 1.) if visible.get(state[0]) == name else (None, None)
        def click(rect):
            name = next(name for name, box in names.items() if box == rect)
            clicked.append(name)
            state[0] = ("stall" if shop_opens_sell else "shop") if name == "shangcheng.png" else "stall"
        with ExitStack() as stack:
            stack.enter_context(patch.object(huoli, 'find_icon_on_screen', side_effect=find))
            stack.enter_context(patch.object(huoli, 'random_click_mouse', side_effect=click))
            stack.enter_context(patch.object(huoli, 'clear_market_hover'))
            stack.enter_context(patch.object(huoli, 'capture_market', return_value=None))
            stack.enter_context(patch.object(huoli, 'market_visible', return_value=True))
            diagnostics = stack.enter_context(patch.object(huoli, 'save_market_diagnostic'))
            stack.enter_context(patch.object(huoli.time, 'sleep'))
            result = huoli.open_baitan_sell((0, 0, 638, 505), 'test')
        return result, clicked, diagnostics.call_count

    def test_full_shop_stall_sell_route(self):
        result, clicks, _ = self.navigate('world')
        self.assertTrue(result)
        self.assertEqual(clicks, ['shangcheng.png', 'baitan.png', 'want_to_chushou.png'])

    def test_visible_sell_tab_skips_shop_and_stall(self):
        result, clicks, _ = self.navigate('stall')
        self.assertTrue(result)
        self.assertEqual(clicks, ['want_to_chushou.png'])

    def test_shop_restores_stall_without_baitan_click(self):
        result, clicks, _ = self.navigate('world', shop_opens_sell=True)
        self.assertTrue(result)
        self.assertEqual(clicks, ['shangcheng.png', 'want_to_chushou.png'])

    def test_missing_navigation_is_bounded(self):
        result, clicks, diagnostics = self.navigate('missing')
        self.assertFalse(result)
        self.assertEqual(clicks, [])
        self.assertEqual(diagnostics, 1)

    def test_phase2_returns_only_windows_with_successful_navigation(self):
        import huoli_utilize as huoli
        windows = [(0, 0, 638, 505), (638, 0, 638, 505)]
        with patch.object(huoli, 'open_baitan_sell', side_effect=[False, True]) as navigate, \
                patch.object(huoli, '_make_ocr') as ocr:
            self.assertEqual(huoli.open_marketplaces(windows), windows[1:])
        self.assertEqual(navigate.call_count, 2)
        ocr.assert_not_called()

    def test_first_listing_duration_confirmation(self):
        import huoli_utilize as huoli
        with patch.object(huoli.time, 'sleep'), \
                patch.object(huoli, 'find_icon_on_screen', side_effect=[((1, 1, 2, 2), 1.),
                    (None, None), ((3, 3, 4, 4), 1.)]), \
                patch.object(huoli, 'random_click_mouse') as click:
            self.assertTrue(huoli.confirm_listing_duration((0, 0, 638, 505)))
        self.assertEqual(click.call_count, 2)


if __name__ == '__main__':
    unittest.main()
