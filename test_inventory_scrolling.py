"""Exercise both inventory loops without importing live GUI automation."""
import ast
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock


class InventoryScrollingTests(unittest.TestCase):
    def test_each_scroll_is_scanned_before_reset(self):
        for filename in ('arrange_inventory_main.py', 'arrange_inventory.py'):
            for budget in (0, 1, 5):
                with self.subTest(filename=filename, budget=budget):
                    self.check_loop(filename, budget)

    def check_loop(self, filename, budget):
        tree = ast.parse(Path(__file__).with_name(filename).read_text(encoding='utf-8'))
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                        and node.name == 'process_inventory_with_scrolling')
        windows = [(0, 0, 640, 480), (640, 0, 640, 480)]
        positions = {window: 0 for window in windows}
        scans = []
        events = []
        medicine = Mock()
        bbox = (10, 10, 20, 20)

        def reset(*args):
            events.append('reset')
            for window in windows:
                positions[window] = 0

        def drag(window, direction, drag_area):
            self.assertEqual(direction, 'down')
            positions[window] += 1
            events.append('drag')

        def scan(*args):
            scans.append(tuple(positions.values()))
            events.append('scan')
            # Earlier empty scans must not stop discovery on the last page.
            if len(scans) == budget + 3:
                return [(bbox, 'medicine', 0.99, 'medicine.png')]
            return []

        find_icon = Mock(return_value=(None, None))
        namespace = dict(
            defaultdict=defaultdict, logger=Mock(), time=Mock(), random=Mock(),
            im=SimpleNamespace(find_icons_from_each_window=scan,
                               find_icon_on_screen=find_icon,
                               find_icon_each_window=Mock(return_value=([], []))),
            window_capture_areas_=windows, reset_inventory_to_top=reset,
            drag_inventory=drag, random_click_mouse=Mock(),
            inventory_unselected_path='tab', inventory_arrange_path='arrange',
            market_close_path='close', print=Mock(),
        )
        exec(compile(ast.Module(body=[function], type_ignores=[]), filename, 'exec'), namespace)
        namespace['process_inventory_with_scrolling'](
            [], windows, (0, 0, 100, 100), {'medicine': medicine}, max_scrolls=budget)

        self.assertEqual(scans, [(0, 0)] * 3 + [(i, i) for i in range(1, budget + 1)])
        self.assertEqual(events.count('drag'), budget * len(windows))
        self.assertEqual(events.count('reset'), 2)
        self.assertEqual(events[-2:], ['scan', 'reset'])
        self.assertEqual(find_icon.call_count, 2 * 2 * len(windows))
        medicine.assert_called_once_with([bbox])


if __name__ == '__main__':
    unittest.main()
