#!/usr/bin/env python3
"""audit_cmt.py — 清点 parts 目录下的互动事件片。

规则：
  * 每片最后一行应以 "_audit 事件行数 数量和" 收尾。
  * 缺尾行（最后一行不是 _audit）的片整片隔离，状态记“缺尾行”。
  * 有尾行但重算的事件行数或数量和对不上的片整片隔离，状态记“不符”。
  * 仅校验通过片的事件进入日统计；跨片重复行按其所在片各自计数，不做去重。
  * 隔离片登记实际事件行数与实际数量和。

用法：
  python3 -I audit_cmt.py [parts_dir] [out_dir]
默认 parts_dir=parts，out_dir=当前目录。
输出：daily.csv、isolated.txt、audit.txt（均写到 out_dir）。
"""

import os
import sys


def main():
    parts_dir = sys.argv[1] if len(sys.argv) > 1 else "parts"
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "."

    names = sorted(
        n
        for n in os.listdir(parts_dir)
        if n.startswith("part-") and os.path.isfile(os.path.join(parts_dir, n))
    )

    isolated = []          # (片名, 状态, 实际事件行数, 实际数量和)
    daily = {}             # 日期 -> [事件数, 数量和]

    pass_parts = 0
    pass_events = 0
    bad_parts = 0
    bad_events = 0
    missing_parts = 0
    missing_events = 0

    for name in names:
        with open(os.path.join(parts_dir, name), "r", encoding="utf-8") as fh:
            lines = [ln.strip() for ln in fh if ln.strip()]

        event_lines = [ln for ln in lines if not ln.startswith("_audit")]
        event_count = len(event_lines)
        qty_sum = 0
        parsed = []  # (日期, 数量)
        for ln in event_lines:
            fields = ln.split()
            qty = int(fields[5])
            qty_sum += qty
            parsed.append((fields[3], qty))

        tail = lines[-1] if lines else ""
        if tail.startswith("_audit"):
            claim = tail.split()
            claimed_count = int(claim[1])
            claimed_sum = int(claim[2])
            if claimed_count == event_count and claimed_sum == qty_sum:
                pass_parts += 1
                pass_events += event_count
                for date, qty in parsed:
                    bucket = daily.setdefault(date, [0, 0])
                    bucket[0] += 1
                    bucket[1] += qty
                continue
            status = "不符"
            bad_parts += 1
            bad_events += event_count
        else:
            status = "缺尾行"
            missing_parts += 1
            missing_events += event_count

        isolated.append((name, status, event_count, qty_sum))

    os.makedirs(out_dir, exist_ok=True)

    # daily.csv：一天一行，日期升序，无表头
    with open(os.path.join(out_dir, "daily.csv"), "w", encoding="utf-8", newline="") as fh:
        for date in sorted(daily):
            count, total = daily[date]
            fh.write(f"{date},{count},{total}\n")

    # isolated.txt：片名升序（names 已排序，隔离顺序天然有序）
    with open(os.path.join(out_dir, "isolated.txt"), "w", encoding="utf-8") as fh:
        for name, status, count, total in isolated:
            fh.write(f"{name} {status} {count} {total}\n")

    # audit.txt：六个审计数
    with open(os.path.join(out_dir, "audit.txt"), "w", encoding="utf-8") as fh:
        fh.write(f"通过片数 {pass_parts}\n")
        fh.write(f"通过事件数 {pass_events}\n")
        fh.write(f"不符片数 {bad_parts}\n")
        fh.write(f"不符事件数 {bad_events}\n")
        fh.write(f"缺尾行片数 {missing_parts}\n")
        fh.write(f"缺尾行事件数 {missing_events}\n")


if __name__ == "__main__":
    main()
