"""Seed error_code_knowledge_map table and update student_number for existing students.

Usage:
    cd /mnt/d/Ubuntu_WSL/Teaching_agent/development
    PYTHONPATH=. /home/lyzhang/miniconda3/envs/pyt0/bin/python scripts/seed_knowledge_map.py
"""
from __future__ import annotations

import asyncio

from app.db import init_db, get_db

MAPPINGS: list[tuple[str, str, str, str, str]] = [
    # E01 基础事实错误
    ("E01", "U03", "圆柱与圆锥", "底面周长C=2πr口算", "3.14×5=17.5（应为15.7）"),
    ("E01", "U04", "比例", "化简比口诀错误", "6×9=48（口诀错）"),
    ("E01", "U06", "整理与复习", "整数小数分数口算", "基本乘法口诀记忆错误"),
    # E02 进位错误
    ("E02", "U03", "圆柱与圆锥", "圆柱体积πr²h中间乘法进位", "3.14×25=68.5（应为78.5，十位进位漏加）"),
    ("E02", "U04", "比例", "解比例交叉相乘多位数进位", "比例式中多位数相乘进位漏加"),
    ("E02", "U06", "整理与复习", "多位数乘法进位", "竖式乘法进位处理不稳定"),
    # E03 退位错误
    ("E03", "U03", "圆柱与圆锥", "表面积计算中退位减法", "圆柱表面积减去底面积时连续退位出错"),
    ("E03", "U06", "整理与复习", "多位数减法退位", "连续退位（如402-178）出错"),
    # E04 数位对齐错误
    ("E04", "U03", "圆柱与圆锥", "π×多位数竖式小数位对齐", "3.14×3.6小数位对不齐"),
    ("E04", "U04", "比例", "比例尺大数计算数位对齐", "100000的零对不齐"),
    # E05 运算顺序错误
    ("E05", "U02", "百分数（二）", "二次打折运算顺序", "3500×80%×80%只乘了一次"),
    ("E05", "U04", "比例", "图形放大面积计算顺序", "放大2倍面积也×2（应为×4）"),
    # E06 小数点/分数单位错误
    ("E06", "U02", "百分数（二）", "折扣/成数小数点位置", "八折=8%（应为80%）"),
    ("E06", "U02", "百分数（二）", "利率百分数计算", "18000×4%=7200（应为720）"),
    ("E06", "U03", "圆柱与圆锥", "π计算小数位数错误", "3.14×25=785（小数点错位）"),
    ("E06", "U04", "比例", "比例尺单位换算km↔cm", "1:500000写成1:50000（少一个零）"),
    # E07 抄题/转写错误
    ("E07", "U03", "圆柱与圆锥", "抄错半径/直径", "把直径当半径抄入公式"),
    ("E07", "U04", "比例", "抄错比例尺数字", "比例尺数字抄写时漏零"),
    # E08 步骤遗漏
    ("E08", "U03", "圆柱与圆锥", "圆锥体积漏×⅓", "圆锥体积=πr²h（漏了×⅓）"),
    ("E08", "U03", "圆柱与圆锥", "表面积漏加底面积", "圆柱表面积=2πrh（漏+2πr²）"),
    ("E08", "U03", "圆柱与圆锥", "水桶只算1个底却加了2个", "无盖容器多加了一个底面积"),
    ("E08", "U02", "百分数（二）", "利息漏乘存期", "5000×2.75%=137.5（漏×3年）"),
    # E09 算理理解不足
    ("E09", "U01", "负数", "负数大小比较方向错", "-3>-1（负数越大越小）"),
    ("E09", "U03", "圆柱与圆锥", "r²算成r×2", "5²=10（应为25）"),
    ("E09", "U04", "比例", "正反比例判断错误", "圆面积与半径判断为正比例（应为r²）"),
    # E10 审题与单位理解错误
    ("E10", "U02", "百分数（二）", "折扣意义混淆", "八折=便宜80%（实为便宜20%）"),
    ("E10", "U03", "圆柱与圆锥", "进一法/去尾法选用错误", "铁皮用料四舍五入（应进一法）"),
    ("E10", "U04", "比例", "比例尺单位换算错误", "km→cm换算多/少零"),
    # E11 习惯性未验算
    ("E11", "U03", "圆柱与圆锥", "多步计算结果未检验", "圆锥体积25.12cm³没发现应是75.36的⅓"),
    ("E11", "U04", "比例", "实际距离量级未检查", "比例尺算出500000cm没换算检验"),
]

STUDENT_NUMBERS = {
    "S001": "202001",
    "S002": "202002",
    "S003": "202003",
    "S004": "202004",
    "S005": "202005",
    "S006": "202006",
    "S007": "202007",
    "S008": "202008",
    "S009": "202009",
    "S010": "202010",
}


async def seed() -> None:
    await init_db()
    async with get_db() as db:
        count_cur = await db.execute("SELECT COUNT(*) FROM error_code_knowledge_map")
        existing = (await count_cur.fetchone())[0]
        if existing > 0:
            print(f"error_code_knowledge_map already has {existing} rows, skipping.")
        else:
            for idx, (error_code, unit_id, unit_title, kp, typical) in enumerate(MAPPINGS):
                row_id = f"EKM{idx + 1:03d}"
                await db.execute(
                    """INSERT INTO error_code_knowledge_map
                       (id, error_code, unit_id, unit_title, knowledge_point, typical_error, sort_order)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (row_id, error_code, unit_id, unit_title, kp, typical, idx + 1),
                )
            print(f"Seeded {len(MAPPINGS)} error_code_knowledge_map rows.")

        updated = 0
        for sid, sno in STUDENT_NUMBERS.items():
            cur = await db.execute(
                "UPDATE students SET student_number = ? WHERE id = ? AND (student_number IS NULL OR student_number = '')",
                (sno, sid),
            )
            if cur.rowcount > 0:
                updated += 1
        if updated:
            print(f"Updated student_number for {updated} students.")
        else:
            print("All students already have student_number values.")

        await db.commit()


if __name__ == "__main__":
    asyncio.run(seed())
