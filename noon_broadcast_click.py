import argparse
import datetime as dt
import time
from zoneinfo import ZoneInfo

import broadcast_mouse as bm

BJ_TZ = ZoneInfo("Asia/Shanghai")


def next_beijing_noon(now_bj: dt.datetime) -> dt.datetime:
    target = now_bj.replace(hour=12, minute=0, second=0, microsecond=0)
    if now_bj >= target:
        target += dt.timedelta(days=1)
    return target


def wait_until_epoch(target_epoch: float) -> None:
    while True:
        remaining = target_epoch - time.time()
        if remaining <= 0:
            return
        if remaining > 1.0:
            time.sleep(remaining - 0.5)
        elif remaining > 0.05:
            time.sleep(remaining - 0.02)
        else:
            # final spin for tighter timing
            time.sleep(0)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Broadcast-click at Beijing noon in FAST mode."
    )
    parser.add_argument("--x", type=int, default=100, help="screen x in master window")
    parser.add_argument("--y", type=int, default=100, help="screen y in master window")
    parser.add_argument(
        "--lead-ms",
        type=int,
        default=100,
        help="fire this many ms before 12:00:00 Beijing (0 means exactly at noon)",
    )
    parser.add_argument(
        "--kind",
        choices=["left", "right", "double_left"],
        default="left",
        help="click type",
    )
    args = parser.parse_args()

    now_bj = dt.datetime.now(BJ_TZ)
    noon_bj = next_beijing_noon(now_bj)
    fire_at_bj = noon_bj - dt.timedelta(milliseconds=max(0, args.lead_ms))
    fire_epoch = fire_at_bj.timestamp()

    bm.FAST_MODE = True

    print(f"[SCHEDULE] now(BJ):   {now_bj.isoformat()}")
    print(f"[SCHEDULE] noon(BJ):  {noon_bj.isoformat()}")
    print(f"[SCHEDULE] fire(BJ):  {fire_at_bj.isoformat()} (lead_ms={args.lead_ms})")
    print(f"[ACTION] FAST_MODE={bm.FAST_MODE}, click={args.kind}, xy=({args.x},{args.y})")

    wait_until_epoch(fire_epoch)

    t_exec_bj = dt.datetime.now(BJ_TZ)
    bm.broadcast_click(args.x, args.y, args.kind, reason="beijing_noon_schedule")
    print(f"[DONE] executed at(BJ): {t_exec_bj.isoformat()}")


if __name__ == "__main__":
    main()
