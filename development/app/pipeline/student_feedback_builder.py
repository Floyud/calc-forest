from __future__ import annotations

from app.schemas import ErrorCode, GuidanceMode, StudentGuidance


QUESTION_BANK: dict[ErrorCode, list[str]] = {
    ErrorCode.BASIC_FACT: [
        "这一步对应的是哪句口诀或哪组基础算式？",
        "你能不用急，先把这一小步单独算一遍吗？",
    ],
    ErrorCode.CARRY: [
        "哪一位相加超过了 9？",
        "满十以后，你有没有把进的 1 写到前一位？",
    ],
    ErrorCode.BORROW: [
        "哪一位不够减，需要先借 1？",
        "借位以后，前一位有没有少 1？",
    ],
    ErrorCode.PLACE_VALUE_ALIGNMENT: [
        "个位、十位、百位有没有对齐？",
        "每一列现在分别表示什么数位？",
    ],
    ErrorCode.OPERATION_ORDER: [
        "这道题第一步应该先算哪里？",
        "你能先把最先算的部分圈出来吗？",
    ],
    ErrorCode.TRANSCRIPTION: [
        "你抄下来的数字和原题里的数字一样吗？",
        "符号有没有看错或写错？",
    ],
    ErrorCode.MISSING_STEP: [
        "你是不是只算到了一部分？",
        "还少哪一步没有写出来或合起来？",
    ],
    ErrorCode.NO_CHECKING: [
        "算完以后，这个答案看起来合理吗？",
        "你能用估算或逆运算再检查一次吗？",
    ],
    ErrorCode.CORRECT: [
        "你这题是怎么检查出自己做对的？",
        "下次遇到同类题，你准备先注意哪一步？",
    ],
}


def build_student_guidance(
    *,
    code: ErrorCode,
    guidance_mode: GuidanceMode,
    diagnosis_feedback: str,
    is_correct: bool,
    practice_count: int,
) -> StudentGuidance:
    questions = QUESTION_BANK.get(code, QUESTION_BANK[ErrorCode.MISSING_STEP])[:2]

    if is_correct:
        message = "这题你已经做对了，我们再回头看看你是怎么检查成功的。"
        key_takeaway = "做对以后也能说清方法，这会让你的计算更稳。"
    else:
        message = f"没关系，我们一步一步来。{diagnosis_feedback}"
        key_takeaway = diagnosis_feedback

    if guidance_mode == GuidanceMode.EXPLORATION:
        next_step = f"先按课堂方法做稳，再试 1 道变式题。当前准备了 {practice_count} 道短练习。"
    elif guidance_mode == GuidanceMode.CHALLENGE:
        next_step = f"先完成标准修正，再想想有没有别的方法。当前准备了 {practice_count} 道短练习。"
    else:
        next_step = f"先把关键一步想清楚，再完成这 {practice_count} 道短练习。"

    return StudentGuidance(
        message=message,
        guiding_questions=questions,
        key_takeaway=key_takeaway,
        next_step=next_step,
    )
