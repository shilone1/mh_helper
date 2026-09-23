"""Offline trace regressions; never move or click the mouse."""

import unittest
from unittest.mock import patch

import cv2
import numpy as np

import trace_input as trace


class TraceTests(unittest.TestCase):
    def test_long_stroke_exceeds_recursive_depth(self):
        mask = np.zeros((3, 2002), dtype=np.uint8)
        mask[1, 1:2001] = 255
        paths = trace.build_trace_paths(mask)
        self.assertEqual(len(paths), 1)
        self.assertEqual(len(paths[0]), 3999)
        self.assertEqual(set(paths[0]), {(x, 1) for x in range(1, 2001)})
        self.assertEqual(paths[0][0], paths[0][-1])
        self.assertTrue(all(max(abs(a - c), abs(b - d)) == 1
                            for (a, b), (c, d) in zip(paths[0], paths[0][1:])))

    def test_branch_and_cycle_preserve_recursive_walk(self):
        mask = np.zeros((12, 12), dtype=np.uint8)
        mask[2:10, 3] = 255
        mask[5, 1:10] = 255
        mask[2, 3:8] = 255
        mask[2:6, 7] = 255
        skeleton = trace._thin(mask)
        component = {tuple(p) for p in np.argwhere(skeleton)}
        offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1),
                   (0, 1), (1, -1), (1, 0), (1, 1)]

        def neighbours(point):
            y, x = point
            return [(y + dy, x + dx) for dy, dx in offsets
                    if (y + dy, x + dx) in component]

        start = min([p for p in component if len(neighbours(p)) == 1] or component)
        walk, visited = [start], set()

        def visit(point):
            for neighbour in neighbours(point):
                edge = frozenset((point, neighbour))
                if edge not in visited:
                    visited.add(edge)
                    walk.append(neighbour)
                    visit(neighbour)
                    walk.append(point)

        visit(start)
        self.assertEqual(trace.build_trace_paths(mask), [[(x, y) for y, x in walk]])

    def test_template_gates_square_detection(self):
        template = cv2.imread(trace.TAYIN_DETECT_PATH)
        screen = np.zeros((300, 400, 3), dtype=np.uint8)
        with patch.object(trace.pyautogui, 'screenshot', return_value=screen), \
                patch.object(trace, 'find_trace_areas') as find_areas:
            self.assertIsNone(trace.detect_trace_areas((100, 200, 400, 300))[1])
            find_areas.assert_not_called()

        height, width = template.shape[:2]
        screen[20:20 + height, 30:30 + width] = template
        rgb = cv2.cvtColor(screen, cv2.COLOR_BGR2RGB)
        with patch.object(trace.pyautogui, 'screenshot', return_value=rgb), \
                patch.object(trace, 'find_trace_areas', return_value=[(50, 60, 210, 220)]):
            self.assertEqual(trace.detect_trace_areas((100, 200, 400, 300))[1],
                             [((50, 60, 210, 220), (150, 260, 310, 420))])

    def test_detected_prompt_without_square_reports_failure(self):
        with patch.object(trace.time, 'sleep'), \
                patch.object(trace, 'detect_trace_areas', return_value=(None, [])), \
                patch.object(trace, 'input_trace_paths') as draw, \
                patch.object(trace, 'click_complete_button') as complete:
            self.assertIs(trace.run_full_trace_procedure((0, 0, 400, 300)), False)
            draw.assert_not_called()
            complete.assert_not_called()


if __name__ == '__main__':
    unittest.main()
