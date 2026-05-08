"""Seed knowledge_points, concept_relations, week_calc_mapping, and problem_bank tables."""
from __future__ import annotations

import asyncio
import json
from app.db import init_db, get_db

KNOWLEDGE_POINTS = [
    # --- Unit 1: 分数乘法 (E01) ---
    {"id": "KP_E01_01", "error_code": "E01", "topic": "分数×整数",
     "description": "分子与整数相乘作分子，分母不变；能约分的先约分",
     "method": "先看分母与整数能否约分，能约则先约分，再用分子乘整数",
     "example": "2/5 × 3 = (2×3)/5 = 6/5 = 1又1/5",
     "prerequisite_ids": [], "difficulty_level": "A", "unit_number": 1, "sort_order": 1},
    {"id": "KP_E01_02", "error_code": "E01", "topic": "分数×分数",
     "description": "分子乘分子，分母乘分母；先约分再计算",
     "method": "交叉约分后再乘，分子乘分子，分母乘分母",
     "example": "2/3 × 3/4 = (2×3)/(3×4) = 1/2（先约分）",
     "prerequisite_ids": ["KP_E01_01"], "difficulty_level": "A", "unit_number": 1, "sort_order": 2},
    {"id": "KP_E01_03", "error_code": "E01", "topic": "分数×小数（先约分）",
     "description": "小数能和分母直接约分时，先约分再算",
     "method": "观察小数与分母是否有公因数，有则先约分",
     "example": "3/4 × 0.8 = 3/4 × 4/5 = 3/5（0.8=4/5）",
     "prerequisite_ids": ["KP_E01_02"], "difficulty_level": "B", "unit_number": 1, "sort_order": 3},
    {"id": "KP_E01_04", "error_code": "E01", "topic": "分数×小数（化小数）",
     "description": "分数能化有限小数时，化成小数相乘",
     "method": "判断分母是否只含2和5的因数，若是则化小数",
     "example": "1/4 × 0.3 = 0.25 × 0.3 = 0.075",
     "prerequisite_ids": ["KP_E01_03"], "difficulty_level": "B", "unit_number": 1, "sort_order": 4},
    {"id": "KP_E01_05", "error_code": "E01", "topic": "分数×小数（化分数）",
     "description": "小数化分数再相乘，最通用",
     "method": "小数化分数后按分数乘法规则计算",
     "example": "2/3 × 0.6 = 2/3 × 3/5 = 2/5",
     "prerequisite_ids": ["KP_E01_03"], "difficulty_level": "B", "unit_number": 1, "sort_order": 5},
    {"id": "KP_E01_06", "error_code": "E01", "topic": "乘法交换律",
     "description": "a×b=b×a",
     "method": "交换因数位置，积不变",
     "example": "2/5 × 1/3 = 1/3 × 2/5 = 2/15",
     "prerequisite_ids": [], "difficulty_level": "A", "unit_number": 1, "sort_order": 6},
    {"id": "KP_E01_07", "error_code": "E01", "topic": "乘法结合律",
     "description": "(a×b)×c=a×(b×c)",
     "method": "三个数相乘，先把前两个数相乘或先把后两个数相乘，积不变",
     "example": "(2/3 × 3/4) × 4/5 = 2/3 × (3/4 × 4/5) = 2/5",
     "prerequisite_ids": ["KP_E01_06"], "difficulty_level": "B", "unit_number": 1, "sort_order": 7},
    {"id": "KP_E01_08", "error_code": "E01", "topic": "乘法分配律",
     "description": "(a+b)×c=a×c+b×c",
     "method": "两个数的和与一个数相乘，可以分别相乘再相加",
     "example": "(1/2 + 1/3) × 6 = 1/2×6 + 1/3×6 = 3+2 = 5",
     "prerequisite_ids": ["KP_E01_01", "KP_E01_02"], "difficulty_level": "B", "unit_number": 1, "sort_order": 8},

    # --- Unit 3: 分数除法 (E02) ---
    {"id": "KP_E02_01", "error_code": "E02", "topic": "倒数概念",
     "description": "乘积为1的两个数互为倒数；1的倒数是1，0没有倒数",
     "method": "求倒数：分子分母颠倒位置",
     "example": "3/5的倒数是5/3，7的倒数是1/7",
     "prerequisite_ids": [], "difficulty_level": "A", "unit_number": 3, "sort_order": 1},
    {"id": "KP_E02_02", "error_code": "E02", "topic": "分数÷整数",
     "description": "等于分数乘这个整数的倒数",
     "method": "除以整数（0除外），等于乘这个整数的倒数",
     "example": "4/5 ÷ 2 = 4/5 × 1/2 = 2/5",
     "prerequisite_ids": ["KP_E01_01"], "difficulty_level": "A", "unit_number": 3, "sort_order": 2},
    {"id": "KP_E02_03", "error_code": "E02", "topic": "分数÷分数",
     "description": "等于乘以除数的倒数（变除为乘）",
     "method": "甲数除以乙数（0除外），等于甲数乘乙数的倒数",
     "example": "2/3 ÷ 4/5 = 2/3 × 5/4 = 5/6",
     "prerequisite_ids": ["KP_E01_02"], "difficulty_level": "A", "unit_number": 3, "sort_order": 3},
    {"id": "KP_E02_04", "error_code": "E02", "topic": "分数混合运算",
     "description": "先乘除后加减，有括号先算括号内",
     "method": "按运算顺序逐步计算，注意约分",
     "example": "1/2 + 1/3 × 3/4 = 1/2 + 1/4 = 3/4",
     "prerequisite_ids": ["KP_E02_02", "KP_E02_03"], "difficulty_level": "B", "unit_number": 3, "sort_order": 4},

    # --- Unit 4: 比 (E04) ---
    {"id": "KP_E04_01", "error_code": "E04", "topic": "求比值",
     "description": "前项÷后项，结果可以是整数、小数或分数",
     "method": "用比的前项除以后项，结果即为比值",
     "example": "3:4的比值 = 3÷4 = 0.75（或3/4）",
     "prerequisite_ids": ["KP_E02_02"], "difficulty_level": "A", "unit_number": 4, "sort_order": 1},
    {"id": "KP_E04_02", "error_code": "E04", "topic": "化简整数比",
     "description": "前项后项同时除以最大公因数",
     "method": "找前项和后项的最大公因数，两项同时除以它",
     "example": "12:18 = (12÷6):(18÷6) = 2:3",
     "prerequisite_ids": [], "difficulty_level": "A", "unit_number": 4, "sort_order": 2},
    {"id": "KP_E04_03", "error_code": "E04", "topic": "化简分数比",
     "description": "乘分母的最小公倍数后化简",
     "method": "前后项同乘分母的最小公倍数化为整数比，再化简",
     "example": "1/3:1/4 = (1/3×12):(1/4×12) = 4:3",
     "prerequisite_ids": ["KP_E04_02"], "difficulty_level": "B", "unit_number": 4, "sort_order": 3},
    {"id": "KP_E04_04", "error_code": "E04", "topic": "化简小数比",
     "description": "先化为整数比再化简",
     "method": "前后项同乘10的幂化为整数比，再按整数比化简",
     "example": "0.6:0.9 = 6:9 = 2:3",
     "prerequisite_ids": ["KP_E04_02"], "difficulty_level": "B", "unit_number": 4, "sort_order": 4},
    {"id": "KP_E04_05", "error_code": "E04", "topic": "按比分配",
     "description": "总份数=各项之和，先算每份再乘对应份数",
     "method": "把比看作份数，总量÷总份数=每份量，每份量×份数=对应量",
     "example": "把120按2:3分配：每份=120÷5=24，24×2=48，24×3=72",
     "prerequisite_ids": ["KP_E04_01"], "difficulty_level": "B", "unit_number": 4, "sort_order": 5},

    # --- Unit 5: 圆 (E07) ---
    {"id": "KP_E07_01", "error_code": "E07", "topic": "圆的周长",
     "description": "C=2πr，π取3.14",
     "method": "已知半径求周长：C=2×3.14×r；已知直径：C=3.14×d",
     "example": "r=5cm，C=2×3.14×5=31.4cm",
     "prerequisite_ids": [], "difficulty_level": "A", "unit_number": 5, "sort_order": 1},
    {"id": "KP_E07_02", "error_code": "E07", "topic": "圆的面积",
     "description": "S=πr²",
     "method": "先算r²，再乘3.14",
     "example": "r=4cm，S=3.14×4²=3.14×16=50.24cm²",
     "prerequisite_ids": [], "difficulty_level": "A", "unit_number": 5, "sort_order": 2},
    {"id": "KP_E07_03", "error_code": "E07", "topic": "环形面积",
     "description": "S=π(R²-r²)",
     "method": "大圆面积减小圆面积：3.14×(R²-r²)",
     "example": "R=5cm, r=3cm，S=3.14×(25-9)=3.14×16=50.24cm²",
     "prerequisite_ids": ["KP_E07_02"], "difficulty_level": "B", "unit_number": 5, "sort_order": 3},

    # --- Unit 6: 百分数 (E05/E06) ---
    {"id": "KP_E05_01", "error_code": "E05", "topic": "分数化百分数",
     "description": "先化小数再化百分数，或化分母为100的分数",
     "method": "分子÷分母得小数，小数点右移两位加%",
     "example": "3/4 = 0.75 = 75%",
     "prerequisite_ids": [], "difficulty_level": "A", "unit_number": 6, "sort_order": 1},
    {"id": "KP_E05_02", "error_code": "E05", "topic": "百分数应用（打折）",
     "description": "原价×折扣百分比=售价",
     "method": "折扣数÷100化为小数，乘原价",
     "example": "原价200元，八折=200×0.8=160元",
     "prerequisite_ids": ["KP_E05_01"], "difficulty_level": "B", "unit_number": 6, "sort_order": 2},
    {"id": "KP_E05_03", "error_code": "E05", "topic": "求百分之几",
     "description": "部分÷整体×100%",
     "method": "用部分量除以总量，结果化为百分数",
     "example": "25是200的百分之几？25÷200=0.125=12.5%",
     "prerequisite_ids": ["KP_E05_01"], "difficulty_level": "B", "unit_number": 6, "sort_order": 3},
    {"id": "KP_E06_01", "error_code": "E06", "topic": "小数↔百分数",
     "description": "小数点右移两位加%，或去%左移两位",
     "method": "小数→百分数：小数点右移两位加%；百分数→小数：去%左移两位",
     "example": "0.35=35%，68%=0.68",
     "prerequisite_ids": ["KP_E05_01"], "difficulty_level": "A", "unit_number": 6, "sort_order": 4},
    {"id": "KP_E06_02", "error_code": "E06", "topic": "分数↔小数",
     "description": "分子÷分母",
     "method": "用分子除以分母得到小数；有限小数化分数用10的幂做分母",
     "example": "3/8=0.375，0.6=6/10=3/5",
     "prerequisite_ids": [], "difficulty_level": "A", "unit_number": 6, "sort_order": 5},

    # --- E09: 分数×小数 ---
    {"id": "KP_E09_01", "error_code": "E09", "topic": "分数×小数（先约分）",
     "description": "小数能和分母直接约分时，先约分再算最简便",
     "method": "一看能否先约分：小数÷分母能除尽则先约分",
     "example": "2.4×3/4=0.6×3=1.8",
     "prerequisite_ids": ["KP_E01_03"], "difficulty_level": "B", "unit_number": 1, "sort_order": 9},
    {"id": "KP_E09_02", "error_code": "E09", "topic": "分数×小数（化小数）",
     "description": "分数能化成有限小数时，化成小数相乘",
     "method": "分母只含2和5的因数时可化有限小数",
     "example": "1/4×0.3=0.25×0.3=0.075",
     "prerequisite_ids": ["KP_E09_01"], "difficulty_level": "B", "unit_number": 1, "sort_order": 10},
    {"id": "KP_E09_03", "error_code": "E09", "topic": "分数×小数（化分数）",
     "description": "小数化分数再相乘，所有情况都适用",
     "method": "小数化分数后按分数乘法计算，最通用但步骤稍多",
     "example": "0.3×2/7=3/10×2/7=3/35",
     "prerequisite_ids": ["KP_E09_01"], "difficulty_level": "B", "unit_number": 1, "sort_order": 11},

    # --- E10: 运算律推广 ---
    {"id": "KP_E10_01", "error_code": "E10", "topic": "乘法分配律",
     "description": "(a+b)×c=a×c+b×c，在分数运算中同样适用",
     "method": "观察算式结构，若含公因数可提取后简化计算",
     "example": "5/6×18=(5×18)/6=15",
     "prerequisite_ids": ["KP_E01_08"], "difficulty_level": "B", "unit_number": 1, "sort_order": 12},
    {"id": "KP_E10_02", "error_code": "E10", "topic": "乘法分配律（提取公因数）",
     "description": "a×c+b×c=(a+b)×c，反向提取公因数",
     "method": "找出两个乘积中相同的因数，提取后先加再乘",
     "example": "3/8×34+3/8×66=3/8×(34+66)=3/8×100=75/2",
     "prerequisite_ids": ["KP_E10_01"], "difficulty_level": "B", "unit_number": 1, "sort_order": 13},
    {"id": "KP_E10_03", "error_code": "E10", "topic": "乘法分配律（凑整）",
     "description": "把一个数拆成两个整数之和，再用分配律",
     "method": "如5/6×19+5/6=5/6×(19+1)=5/6×20=50/3",
     "example": "5/6×19+5/6=5/6×20=50/3",
     "prerequisite_ids": ["KP_E10_02"], "difficulty_level": "C", "unit_number": 1, "sort_order": 14},
]

CONCEPT_RELATIONS = [
    {"id": "CR_01", "source_id": "KP_E01_01", "target_id": "KP_E01_02",
     "relation_type": "prerequisite", "weight": 1.0},
    {"id": "CR_02", "source_id": "KP_E01_02", "target_id": "KP_E01_03",
     "relation_type": "prerequisite", "weight": 1.0},
    {"id": "CR_03", "source_id": "KP_E01_01", "target_id": "KP_E02_02",
     "relation_type": "prerequisite", "weight": 0.9},
    {"id": "CR_04", "source_id": "KP_E01_02", "target_id": "KP_E02_03",
     "relation_type": "prerequisite", "weight": 0.9},
    {"id": "CR_05", "source_id": "KP_E02_01", "target_id": "KP_E02_02",
     "relation_type": "prerequisite", "weight": 1.0},
    {"id": "CR_06", "source_id": "KP_E02_01", "target_id": "KP_E02_03",
     "relation_type": "prerequisite", "weight": 1.0},
    {"id": "CR_07", "source_id": "KP_E04_01", "target_id": "KP_E02_02",
     "relation_type": "related", "weight": 0.7},
    {"id": "CR_08", "source_id": "KP_E01_08", "target_id": "KP_E02_04",
     "relation_type": "prerequisite", "weight": 0.8},
    {"id": "CR_09", "source_id": "KP_E05_01", "target_id": "KP_E06_01",
     "relation_type": "prerequisite", "weight": 0.9},
    {"id": "CR_10", "source_id": "KP_E04_02", "target_id": "KP_E04_03",
     "relation_type": "prerequisite", "weight": 1.0},
    {"id": "CR_11", "source_id": "KP_E04_02", "target_id": "KP_E04_04",
     "relation_type": "prerequisite", "weight": 1.0},
    {"id": "CR_12", "source_id": "KP_E04_01", "target_id": "KP_E04_05",
     "relation_type": "prerequisite", "weight": 0.8},
    {"id": "CR_13", "source_id": "KP_E07_02", "target_id": "KP_E07_03",
     "relation_type": "extends", "weight": 1.0},
    {"id": "CR_14", "source_id": "KP_E01_06", "target_id": "KP_E01_07",
     "relation_type": "prerequisite", "weight": 1.0},
    {"id": "CR_15", "source_id": "KP_E06_02", "target_id": "KP_E05_01",
     "relation_type": "prerequisite", "weight": 0.8},
    {"id": "CR_16", "source_id": "KP_E01_03", "target_id": "KP_E01_04",
     "relation_type": "method_of", "weight": 0.6},
    {"id": "CR_17", "source_id": "KP_E01_03", "target_id": "KP_E01_05",
     "relation_type": "method_of", "weight": 0.6},
    {"id": "CR_18", "source_id": "KP_E05_01", "target_id": "KP_E05_02",
     "relation_type": "prerequisite", "weight": 0.9},
    {"id": "CR_19", "source_id": "KP_E05_01", "target_id": "KP_E05_03",
     "relation_type": "prerequisite", "weight": 0.9},
    {"id": "CR_20", "source_id": "KP_E01_01", "target_id": "KP_E04_02",
     "relation_type": "related", "weight": 0.5},
    {"id": "CR_21", "source_id": "KP_E01_03", "target_id": "KP_E09_01",
     "relation_type": "extends", "weight": 1.0},
    {"id": "CR_22", "source_id": "KP_E09_01", "target_id": "KP_E09_02",
     "relation_type": "method_of", "weight": 0.8},
    {"id": "CR_23", "source_id": "KP_E09_01", "target_id": "KP_E09_03",
     "relation_type": "method_of", "weight": 0.8},
    {"id": "CR_24", "source_id": "KP_E01_08", "target_id": "KP_E10_01",
     "relation_type": "extends", "weight": 1.0},
    {"id": "CR_25", "source_id": "KP_E10_01", "target_id": "KP_E10_02",
     "relation_type": "prerequisite", "weight": 0.9},
    {"id": "CR_26", "source_id": "KP_E10_02", "target_id": "KP_E10_03",
     "relation_type": "prerequisite", "weight": 0.9},
]

WEEK_CALC_MAPPING = [
    {"week_start": 1, "week_end": 3, "calc_type": "分数乘法",
     "calc_subtypes": ["乘整数", "乘分数", "乘小数"],
     "error_codes": ["E01"], "is_review": 0, "review_types": []},
    {"week_start": 4, "week_end": 4, "calc_type": "滚动：分数乘法",
     "calc_subtypes": ["乘加混合", "运算律"],
     "error_codes": ["E01"], "is_review": 1, "review_types": ["分数乘法"]},
    {"week_start": 5, "week_end": 7, "calc_type": "分数除法",
     "calc_subtypes": ["÷整数", "÷分数", "乘除混合"],
     "error_codes": ["E02"], "is_review": 0, "review_types": []},
    {"week_start": 8, "week_end": 9, "calc_type": "比",
     "calc_subtypes": ["化简比", "求比值", "按比分配"],
     "error_codes": ["E04"], "is_review": 0, "review_types": []},
    {"week_start": 10, "week_end": 12, "calc_type": "圆",
     "calc_subtypes": ["π×整数", "周长", "面积"],
     "error_codes": ["E07"], "is_review": 0, "review_types": []},
    {"week_start": 13, "week_end": 15, "calc_type": "百分数",
     "calc_subtypes": ["互化", "四则计算", "打折"],
     "error_codes": ["E05", "E06"], "is_review": 0, "review_types": []},
    {"week_start": 16, "week_end": 16, "calc_type": "滚动：分数+百分数",
     "calc_subtypes": ["综合"],
     "error_codes": ["E01", "E02", "E05", "E06"], "is_review": 1,
     "review_types": ["分数+百分数"]},
    {"week_start": 17, "week_end": 17, "calc_type": "滚动：圆+比+百分数",
     "calc_subtypes": ["综合"],
     "error_codes": ["E04", "E05", "E06", "E07"], "is_review": 1,
     "review_types": ["圆+比+百分数"]},
    {"week_start": 18, "week_end": 20, "calc_type": "综合复习",
     "calc_subtypes": ["全部"],
     "error_codes": ["E01", "E02", "E03", "E04", "E05", "E06", "E07", "E08", "E11"],
     "is_review": 1, "review_types": ["全部"]},
]

PROBLEM_BANK = [
    # E01 - 分数乘法
    {"id": "PB_E01_01", "problem_text": "2/5×3=", "problem_plain": "2/5×3=",
     "correct_answer": "6/5", "error_code": "E01", "knowledge_point": "分数×整数",
     "difficulty": "A", "method": "分子×整数，分母不变", "source": "system"},
    {"id": "PB_E01_02", "problem_text": "3/4×2/5=", "problem_plain": "3/4×2/5=",
     "correct_answer": "3/10", "error_code": "E01", "knowledge_point": "分数×分数",
     "difficulty": "A", "method": "交叉约分再乘", "source": "system"},
    {"id": "PB_E01_03", "problem_text": "5/6×3/10=", "problem_plain": "5/6×3/10=",
     "correct_answer": "1/4", "error_code": "E01", "knowledge_point": "分数×分数",
     "difficulty": "A", "method": "交叉约分：5和10约，6和3约", "source": "system"},
    {"id": "PB_E01_04", "problem_text": "3/5×0.4=", "problem_plain": "3/5×0.4=",
     "correct_answer": "6/25", "error_code": "E01", "knowledge_point": "分数×小数（先约分）",
     "difficulty": "B", "method": "5和0.4约分得0.08，3×0.08=0.24", "source": "system"},
    {"id": "PB_E01_05", "problem_text": "1/4×0.3=", "problem_plain": "1/4×0.3=",
     "correct_answer": "0.075", "error_code": "E01", "knowledge_point": "分数×小数（化小数）",
     "difficulty": "B", "method": "1/4=0.25, 0.25×0.3=0.075", "source": "system"},
    {"id": "PB_E01_06", "problem_text": "2/3×0.6=", "problem_plain": "2/3×0.6=",
     "correct_answer": "2/5", "error_code": "E01", "knowledge_point": "分数×小数（化分数）",
     "difficulty": "B", "method": "0.6=3/5, 2/3×3/5=2/5", "source": "system"},
    {"id": "PB_E01_07", "problem_text": "(1/2+1/3)×6=", "problem_plain": "(1/2+1/3)×6=",
     "correct_answer": "5", "error_code": "E01", "knowledge_point": "乘法分配律",
     "difficulty": "B", "method": "1/2×6+1/3×6=3+2=5", "source": "system"},
    {"id": "PB_E01_08", "problem_text": "7/12×8/21=", "problem_plain": "7/12×8/21=",
     "correct_answer": "2/9", "error_code": "E01", "knowledge_point": "分数×分数",
     "difficulty": "B", "method": "7和21约，12和8约", "source": "system"},

    # E02 - 分数除法
    {"id": "PB_E02_01", "problem_text": "4/5÷2=", "problem_plain": "4/5÷2=",
     "correct_answer": "2/5", "error_code": "E02", "knowledge_point": "分数÷整数",
     "difficulty": "A", "method": "乘以2的倒数1/2", "source": "system"},
    {"id": "PB_E02_02", "problem_text": "2/3÷4/5=", "problem_plain": "2/3÷4/5=",
     "correct_answer": "5/6", "error_code": "E02", "knowledge_point": "分数÷分数",
     "difficulty": "A", "method": "变除为乘：2/3×5/4=5/6", "source": "system"},
    {"id": "PB_E02_03", "problem_text": "5/6÷5/8=", "problem_plain": "5/6÷5/8=",
     "correct_answer": "4/3", "error_code": "E02", "knowledge_point": "分数÷分数",
     "difficulty": "A", "method": "5/6×8/5=8/6=4/3", "source": "system"},
    {"id": "PB_E02_04", "problem_text": "1/2+1/3×3/4=", "problem_plain": "1/2+1/3×3/4=",
     "correct_answer": "3/4", "error_code": "E02", "knowledge_point": "分数混合运算",
     "difficulty": "B", "method": "先乘除后加减：1/3×3/4=1/4，1/2+1/4=3/4", "source": "system"},
    {"id": "PB_E02_05", "problem_text": "3/4÷(1/2+1/4)=", "problem_plain": "3/4÷(1/2+1/4)=",
     "correct_answer": "1", "error_code": "E02", "knowledge_point": "分数混合运算",
     "difficulty": "B", "method": "先算括号：1/2+1/4=3/4，3/4÷3/4=1", "source": "system"},

    # E04 - 比
    {"id": "PB_E04_01", "problem_text": "求比值 15:20", "problem_plain": "15:20=",
     "correct_answer": "3/4", "error_code": "E04", "knowledge_point": "求比值",
     "difficulty": "A", "method": "15÷20=3/4", "source": "system"},
    {"id": "PB_E04_02", "problem_text": "化简比 12:18", "problem_plain": "化简 12:18",
     "correct_answer": "2:3", "error_code": "E04", "knowledge_point": "化简整数比",
     "difficulty": "A", "method": "最大公因数6，12÷6:18÷6=2:3", "source": "system"},
    {"id": "PB_E04_03", "problem_text": "化简比 1/3:1/4", "problem_plain": "化简 1/3:1/4",
     "correct_answer": "4:3", "error_code": "E04", "knowledge_point": "化简分数比",
     "difficulty": "B", "method": "同乘12得4:3", "source": "system"},
    {"id": "PB_E04_04", "problem_text": "化简比 0.6:0.9", "problem_plain": "化简 0.6:0.9",
     "correct_answer": "2:3", "error_code": "E04", "knowledge_point": "化简小数比",
     "difficulty": "B", "method": "同乘10得6:9=2:3", "source": "system"},
    {"id": "PB_E04_05", "problem_text": "把120按2:3分配", "problem_plain": "120按2:3分配",
     "correct_answer": "48和72", "error_code": "E04", "knowledge_point": "按比分配",
     "difficulty": "B", "method": "120÷5=24, 24×2=48, 24×3=72", "source": "system"},

    # E05 - 百分数
    {"id": "PB_E05_01", "problem_text": "3/4化为百分数", "problem_plain": "3/4=?%",
     "correct_answer": "75%", "error_code": "E05", "knowledge_point": "分数化百分数",
     "difficulty": "A", "method": "3÷4=0.75=75%", "source": "system"},
    {"id": "PB_E05_02", "problem_text": "原价200元打八折", "problem_plain": "200×80%=",
     "correct_answer": "160", "error_code": "E05", "knowledge_point": "百分数应用（打折）",
     "difficulty": "B", "method": "200×0.8=160", "source": "system"},
    {"id": "PB_E05_03", "problem_text": "25是200的百分之几", "problem_plain": "25÷200=?%",
     "correct_answer": "12.5%", "error_code": "E05", "knowledge_point": "求百分之几",
     "difficulty": "B", "method": "25÷200=0.125=12.5%", "source": "system"},

    # E06 - 小数分数百分数互化
    {"id": "PB_E06_01", "problem_text": "0.35化为百分数", "problem_plain": "0.35=?%",
     "correct_answer": "35%", "error_code": "E06", "knowledge_point": "小数↔百分数",
     "difficulty": "A", "method": "小数点右移两位加%", "source": "system"},
    {"id": "PB_E06_02", "problem_text": "68%化为小数", "problem_plain": "68%=?",
     "correct_answer": "0.68", "error_code": "E06", "knowledge_point": "小数↔百分数",
     "difficulty": "A", "method": "去%左移两位", "source": "system"},
    {"id": "PB_E06_03", "problem_text": "3/8化为小数", "problem_plain": "3/8=?",
     "correct_answer": "0.375", "error_code": "E06", "knowledge_point": "分数↔小数",
     "difficulty": "A", "method": "3÷8=0.375", "source": "system"},
    {"id": "PB_E06_04", "problem_text": "0.6化为分数", "problem_plain": "0.6=/?",
     "correct_answer": "3/5", "error_code": "E06", "knowledge_point": "分数↔小数",
     "difficulty": "A", "method": "6/10=3/5", "source": "system"},

    # E07 - 圆
    {"id": "PB_E07_01", "problem_text": "r=5cm,求周长", "problem_plain": "C=2×3.14×5=",
     "correct_answer": "31.4cm", "error_code": "E07", "knowledge_point": "圆的周长",
     "difficulty": "A", "method": "C=2×3.14×5=31.4", "source": "system"},
    {"id": "PB_E07_02", "problem_text": "r=4cm,求面积", "problem_plain": "S=3.14×4²=",
     "correct_answer": "50.24cm²", "error_code": "E07", "knowledge_point": "圆的面积",
     "difficulty": "A", "method": "S=3.14×16=50.24", "source": "system"},
    {"id": "PB_E07_03", "problem_text": "R=5cm,r=3cm,求环形面积", "problem_plain": "S=3.14×(25-9)=",
     "correct_answer": "50.24cm²", "error_code": "E07", "knowledge_point": "环形面积",
     "difficulty": "B", "method": "3.14×(25-9)=3.14×16=50.24", "source": "system"},
    {"id": "PB_E07_04", "problem_text": "d=10cm,求周长", "problem_plain": "C=3.14×10=",
     "correct_answer": "31.4cm", "error_code": "E07", "knowledge_point": "圆的周长",
     "difficulty": "A", "method": "C=3.14×d=31.4", "source": "system"},

    # E03 - 退位错误 (mixed subtraction)
    {"id": "PB_E03_01", "problem_text": "402-178=", "problem_plain": "402-178=",
     "correct_answer": "224", "error_code": "E03", "knowledge_point": "退位减法",
     "difficulty": "A", "method": "个位12-8=4,十位9-7=2,百位3-1=2", "source": "system"},
    {"id": "PB_E03_02", "problem_text": "530-267=", "problem_plain": "530-267=",
     "correct_answer": "263", "error_code": "E03", "knowledge_point": "退位减法",
     "difficulty": "A", "method": "连续退位：个位10-7=3,十位12-6=6,百位4-2=2", "source": "system"},

    # E08 - 步骤遗漏
    {"id": "PB_E08_01", "problem_text": "2/3+1/4×4/5=", "problem_plain": "2/3+1/4×4/5=",
     "correct_answer": "17/15", "error_code": "E08", "knowledge_point": "分数混合运算",
     "difficulty": "B", "method": "先算乘法1/4×4/5=1/5, 再2/3+1/5=10/15+3/15=13/15", "source": "system"},
]


async def seed():
    await init_db()
    async with get_db() as db:
        # --- knowledge_points ---
        kp_count = 0
        for kp in KNOWLEDGE_POINTS:
            await db.execute(
                """INSERT OR IGNORE INTO knowledge_points
                   (id, error_code, topic, description, method, example,
                    prerequisite_ids, difficulty_level, unit_number, sort_order)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (kp["id"], kp["error_code"], kp["topic"], kp["description"],
                 kp["method"], kp["example"],
                 json.dumps(kp["prerequisite_ids"], ensure_ascii=False),
                 kp["difficulty_level"], kp["unit_number"], kp["sort_order"]),
            )
            kp_count += 1

        # --- FTS5 index for knowledge points ---
        for kp in KNOWLEDGE_POINTS:
            await db.execute(
                """INSERT OR IGNORE INTO knowledge_points_fts (id, topic, description, method, example)
                   VALUES (?, ?, ?, ?, ?)""",
                (kp["id"], kp["topic"], kp["description"], kp["method"], kp["example"]),
            )

        # --- concept_relations ---
        cr_count = 0
        for cr in CONCEPT_RELATIONS:
            await db.execute(
                """INSERT OR IGNORE INTO concept_relations
                   (id, source_id, target_id, relation_type, weight)
                   VALUES (?, ?, ?, ?, ?)""",
                (cr["id"], cr["source_id"], cr["target_id"],
                 cr["relation_type"], cr["weight"]),
            )
            cr_count += 1

        # --- week_calc_mapping ---
        wc_count = 0
        for i, wc in enumerate(WEEK_CALC_MAPPING, 1):
            row_id = f"WCM_{i:03d}"
            await db.execute(
                """INSERT OR IGNORE INTO week_calc_mapping
                   (id, week_start, week_end, calc_type, calc_subtypes,
                    error_codes, is_review, review_types, semester, grade)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (row_id, wc["week_start"], wc["week_end"], wc["calc_type"],
                 json.dumps(wc["calc_subtypes"], ensure_ascii=False),
                 json.dumps(wc["error_codes"], ensure_ascii=False),
                 wc["is_review"],
                 json.dumps(wc["review_types"], ensure_ascii=False),
                 1, 6),
            )
            wc_count += 1

        # --- problem_bank ---
        pb_count = 0
        for pb in PROBLEM_BANK:
            await db.execute(
                """INSERT OR IGNORE INTO problem_bank
                   (id, problem_text, problem_plain, correct_answer, error_code,
                    knowledge_point, difficulty, method, source)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (pb["id"], pb["problem_text"], pb["problem_plain"],
                 pb["correct_answer"], pb["error_code"], pb["knowledge_point"],
                 pb["difficulty"], pb["method"], pb["source"]),
            )
            pb_count += 1

        await db.commit()
        print(f"✅ Seeded: {kp_count} knowledge_points, {cr_count} concept_relations, "
              f"{wc_count} week_calc_mappings, {pb_count} problem_bank entries")


if __name__ == "__main__":
    asyncio.run(seed())
