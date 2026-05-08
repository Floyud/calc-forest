from __future__ import annotations

import ast
import operator
import re
from dataclasses import dataclass
from fractions import Fraction

from app.schemas import (
    ERROR_LABELS,
    AnswerRecord,
    DiagnosisResponse,
    ErrorCode,
    ErrorTag,
)


_DIGIT_RE = re.compile(r"\d+(?:\.\d+)?")
_EXPR_RE = re.compile(r"^[\d\s+\-*/×÷().]+$")


@dataclass(frozen=True)
class ComputedValues:
    expected: Fraction | None
    student: Fraction | None
    no_precedence: Fraction | None


def diagnose_answer(record: AnswerRecord) -> DiagnosisResponse:
    expected = _parse_number(record.correct_answer)
    student = _parse_number(record.student_answer)
    expression = _extract_expression(record.problem)
    computed = ComputedValues(
        expected=expected,
        student=student,
        no_precedence=_eval_left_to_right(expression) if expression else None,
    )

    is_correct = expected is not None and student is not None and expected == student
    if is_correct:
        tag = _tag(
            ErrorCode.CORRECT,
            0.99,
            "学生答案与标准答案一致。",
            "可进入同知识点变式巩固，保持少量练习。",
            "这题已经做对了，订正时可以说一说你用了哪一步检查。",
        )
        return _response(record, True, tag, [], computed)

    checks = [
        _detect_transcription,
        _detect_operation_order,
        _detect_borrow,
        _detect_carry,
        _detect_place_value_alignment,
        _detect_decimal_error,
        _detect_basic_fact,
        _detect_missing_step,
        _detect_no_checking,
    ]
    tags: list[ErrorTag] = []
    for check in checks:
        tag = check(record, expression, computed)
        if tag is not None and all(tag.code != item.code for item in tags):
            tags.append(tag)

    if not tags:
        tags.append(
            _tag(
                ErrorCode.UNKNOWN,
                0.45,
                "当前规则未找到稳定错因，需要教师查看学生步骤。",
                "建议补充学生竖式或中间步骤后重新诊断。",
                "把中间步骤写出来，老师可以更准确地帮你找到问题。",
            )
        )

    primary, *secondary = sorted(tags, key=lambda item: item.confidence, reverse=True)
    return _response(record, False, primary, secondary[:2], computed)


def _response(
    record: AnswerRecord,
    is_correct: bool,
    primary: ErrorTag,
    secondary: list[ErrorTag],
    computed: ComputedValues,
) -> DiagnosisResponse:
    secondary_text = ""
    if secondary:
        secondary_text = "；可能还伴随" + "、".join(tag.label for tag in secondary)
    teacher_summary = (
        f"{record.student_id} 本题{'正确' if is_correct else '错误'}。"
        f"主要判断：{primary.label}{secondary_text}。证据：{primary.evidence}"
    )
    return DiagnosisResponse(
        record_id=record.record_id,
        student_id=record.student_id,
        is_correct=is_correct,
        primary_error=primary,
        secondary_errors=secondary,
        normalized={
            "expected_value": _fraction_to_json(computed.expected),
            "student_value": _fraction_to_json(computed.student),
            "left_to_right_value": _fraction_to_json(computed.no_precedence),
        },
        teacher_summary=teacher_summary,
    )


def _detect_operation_order(
    record: AnswerRecord, expression: str | None, computed: ComputedValues
) -> ErrorTag | None:
    if not expression or computed.student is None or computed.no_precedence is None:
        return None
    if "/" in record.correct_answer or "/" in record.student_answer:
        return None
    if computed.expected != computed.no_precedence and computed.student == computed.no_precedence:
        return _tag(
            ErrorCode.OPERATION_ORDER,
            0.9,
            f"学生答案等于从左到右依次计算的结果 {computed.no_precedence}，但标准答案需要先乘除后加减或先算括号。",
            "让学生先在算式上标出第一步、第二步，再计算。",
            "先圈出要最先计算的部分，再一步一步写。",
        )
    return None


def _detect_borrow(
    record: AnswerRecord, expression: str | None, computed: ComputedValues
) -> ErrorTag | None:
    if not expression or "-" not in expression or computed.student is None:
        return None
    numbers = _integer_numbers(expression)
    if len(numbers) != 2:
        return None
    a, b = numbers
    if a < b:
        return None
    if _needs_borrow(a, b):
        no_borrow = _subtract_without_borrow(a, b)
        if computed.student == Fraction(no_borrow, 1):
            return _tag(
                ErrorCode.BORROW,
                0.92,
                f"{a}-{b} 需要退位，学生答案符合未退位逐位相减的结果 {no_borrow}。",
                "用数位表复盘退位过程，先练 3-5 道同结构题。",
                "看到本位不够减时，先向前一位借 1，再继续算。",
            )
        if abs(float(computed.student - Fraction(a - b, 1))) >= 10:
            return _tag(
                ErrorCode.BORROW,
                0.74,
                f"{a}-{b} 存在需要退位的数位，学生结果与标准答案偏差较大。",
                "检查每个不够减的位置是否完成退位和被借位减一。",
                "逐位检查：哪一位不够减？借位后前一位有没有少 1？",
            )
    return None


def _detect_carry(
    record: AnswerRecord, expression: str | None, computed: ComputedValues
) -> ErrorTag | None:
    if not expression or "+" not in expression or computed.student is None:
        return None
    numbers = _integer_numbers(expression)
    if len(numbers) != 2:
        return None
    a, b = numbers
    if _needs_carry(a, b):
        no_carry = _add_without_carry(a, b)
        if computed.student == Fraction(no_carry, 1):
            return _tag(
                ErrorCode.CARRY,
                0.92,
                f"{a}+{b} 需要进位，学生答案符合未处理进位的结果 {no_carry}。",
                "让学生在竖式中显式写出进位数字，再做同位练习。",
                "哪一位满十，就要向前一位进 1。",
            )
        if computed.student < Fraction(a + b, 1):
            return _tag(
                ErrorCode.CARRY,
                0.72,
                f"{a}+{b} 存在满十进位，学生结果小于正确和，可能漏加进位。",
                "复查每个满十的位置，要求学生写出进位标记。",
                "检查有没有一位相加超过 9，超过就要进位。",
            )
    return None


def _detect_basic_fact(
    record: AnswerRecord, expression: str | None, computed: ComputedValues
) -> ErrorTag | None:
    if computed.student is None or computed.expected is None:
        return None
    if expression:
        numbers = _integer_numbers(expression)
        simple_problem = len(numbers) == 2 and all(0 <= n <= 20 for n in numbers)
        if simple_problem and any(op in expression for op in ["+", "-", "*", "×", "/", "÷"]):
            return _tag(
                ErrorCode.BASIC_FACT,
                0.78,
                "题目属于低位基础计算，错误更可能来自口诀、口算事实或基本加减事实提取。",
                "安排短时、低负荷的基础事实练习，并让学生说出计算依据。",
                "先把这类基础算式练稳，再做更长的题。",
            )
        if "/" in expression and len(numbers) == 2 and numbers[1] and numbers[0] % numbers[1] == 0:
            quotient = numbers[0] // numbers[1]
            if numbers[1] <= 12 and quotient <= 12:
                return _tag(
                    ErrorCode.BASIC_FACT,
                    0.76,
                    "题目属于基础除法事实，学生答案不符合对应乘除关系。",
                    "回到乘法口诀和乘除互逆关系进行短时练习。",
                    "可以用乘法检查除法：除数乘答案能不能回到被除数？",
                )
    return None


def _detect_place_value_alignment(
    record: AnswerRecord, expression: str | None, computed: ComputedValues
) -> ErrorTag | None:
    if computed.student is None or computed.expected is None:
        return None
    step_text = " ".join(record.student_steps).lower()
    alignment_markers = ["align", "aligned", "under", "place value", "对齐", "数位", "位值"]
    if any(marker in step_text for marker in alignment_markers):
        return _tag(
            ErrorCode.PLACE_VALUE_ALIGNMENT,
            0.8,
            "学生步骤中出现数位放置或对齐相关描述，且最终答案错误，疑似数位对齐问题。",
            "用数位表或方格纸重新书写竖式，强调个位对个位、十位对十位。",
            "写竖式时先对齐个位，再检查每一列代表什么数位。",
        )
    if abs(computed.expected) >= 100 and computed.student in {
        computed.expected * 10,
        computed.expected / 10,
        computed.expected + 9,
        computed.expected - 9,
        computed.expected + 90,
        computed.expected - 90,
    }:
        return _tag(
            ErrorCode.PLACE_VALUE_ALIGNMENT,
            0.68,
            "学生答案与标准答案呈现 10 倍、十分之一或整十位偏移特征，疑似数位对齐问题。",
            "用数位表或方格纸重新书写竖式，强调个位对个位、十位对十位。",
            "写竖式时先对齐个位，再检查每一列代表什么数位。",
        )
    return None


def _detect_decimal_error(
    record: AnswerRecord, expression: str | None, computed: ComputedValues
) -> ErrorTag | None:
    if computed.student is None or computed.expected is None:
        return None
    has_decimal = "." in record.problem or "." in record.correct_answer or "." in record.student_answer
    if has_decimal and computed.expected != 0:
        ratio = computed.student / computed.expected
        if ratio in {Fraction(10, 1), Fraction(1, 10), Fraction(100, 1), Fraction(1, 100)}:
            return _tag(
                ErrorCode.DECIMAL_FRACTION_UNIT,
                0.86,
                "学生答案与标准答案相差 10 倍或 100 倍，符合小数点位置错误特征。",
                "让学生先估算结果范围，再确定小数点位置。",
                "先估一估答案大概是多少，再写小数点。",
            )
        return _tag(
            ErrorCode.DECIMAL_FRACTION_UNIT,
            0.64,
            "题目或答案包含小数，学生答案不正确，需优先复核小数点位置和数位对齐。",
            "先估算结果范围，再检查小数点和相同数位是否对齐。",
            "先估一估答案应该比哪些数大、比哪些数小。",
        )
    has_fraction = "/" in record.problem or "/" in record.correct_answer or "/" in record.student_answer
    if has_fraction and computed.expected != computed.student:
        return _tag(
            ErrorCode.DECIMAL_FRACTION_UNIT,
            0.68,
            "题目或答案包含分数，学生答案不正确，可能混淆了分数单位或分子分母处理方式。",
            "用同分母/通分步骤复盘，强调分数单位一致后再计算。",
            "先想一想每个分数的单位是不是一样，再决定能不能直接相加减。",
        )
    return None


def _detect_transcription(
    record: AnswerRecord, expression: str | None, computed: ComputedValues
) -> ErrorTag | None:
    if not record.student_steps:
        return None
    problem_numbers = set(_DIGIT_RE.findall(record.problem))
    step_text = " ".join(record.student_steps)
    normalized_step = _normalize_math_text(step_text)
    explicit_markers = ["抄", "看成", "写成", "copy", "copied", "read as", "wrote as"]
    has_marker = any(marker in normalized_step.lower() for marker in explicit_markers)
    step_expressions = re.findall(r"\d+(?:\.\d+)?(?:\s*[+\-*/]\s*\d+(?:\.\d+)?)+", normalized_step)

    if problem_numbers and step_expressions:
        expression_numbers: list[str] = []
        for item in step_expressions:
            expression_numbers.extend(_DIGIT_RE.findall(item))
        unexpected = [n for n in expression_numbers if n not in problem_numbers]
        if unexpected and has_marker:
            return _tag(
                ErrorCode.TRANSCRIPTION,
                0.86,
                f"学生步骤明确出现转写信号，且算式中有原题没有的数字 {unexpected[:3]}。",
                "要求学生先圈出原题数字和符号，再誊写算式。",
                "先对照题目检查数字和符号有没有抄错。",
            )
        if unexpected and _looks_like_word_problem(record.problem):
            return _tag(
                ErrorCode.TRANSCRIPTION,
                0.78,
                f"学生列式中使用了原题没有的数量 {unexpected[:3]}，疑似从应用题条件转写时出错。",
                "要求学生先圈出原题数字和符号，再誊写算式。",
                "先对照题目检查数字和符号有没有抄错。",
            )
    return None


def _looks_like_word_problem(problem: str) -> bool:
    letters = [char for char in problem.lower() if char.isalpha() and char != "x"]
    return bool(letters) or any(
        marker in problem for marker in ["一共", "还剩", "平均", "多少", "几"]
    )


def _detect_missing_step(
    record: AnswerRecord, expression: str | None, computed: ComputedValues
) -> ErrorTag | None:
    if not record.student_steps and expression and any(op in expression for op in ["+", "-", "*", "×", "/", "÷"]):
        return _tag(
            ErrorCode.MISSING_STEP,
            0.55,
            "学生未提供中间步骤，当前只能根据最终答案推断，诊断证据不足。",
            "要求学生补写关键步骤，再判断是计算错误还是方法错误。",
            "把中间步骤写出来，方便检查是哪一步开始出错。",
        )
    if expression and computed.student is not None and computed.expected is not None:
        expected_text = str(computed.expected.numerator)
        student_text = str(computed.student.numerator)
        numbers = _integer_numbers(expression)
        if "*" in expression and len(numbers) == 2:
            a, b = numbers
            partials = {a * (b % 10), a * (b // 10), b * (a % 10), b * (a // 10)}
            if int(computed.student) in partials:
                return _tag(
                    ErrorCode.MISSING_STEP,
                    0.78,
                    "学生答案等于乘法中的一个部分积，可能遗漏了另一部分积或合并步骤。",
                    "要求学生补齐每个部分积，并检查第二行部分积是否需要错位。",
                    "乘两位数时不要只算一位，还要把两个部分积合起来。",
                )
        multi_digit_mul_div = any(op in expression for op in ["*", "/"]) and any(n >= 10 for n in numbers)
        if multi_digit_mul_div and student_text and student_text in expected_text and student_text != expected_text:
            return _tag(
                ErrorCode.MISSING_STEP,
                0.72,
                "学生答案像是只保留了部分计算结果，可能遗漏了一个中间步骤或部分积/商位。",
                "要求学生补齐竖式中的每个部分积、商位或余数处理步骤。",
                "检查有没有只算了一部分，还没有把所有步骤合起来。",
            )
    return None


def _detect_no_checking(
    record: AnswerRecord, expression: str | None, computed: ComputedValues
) -> ErrorTag | None:
    if computed.student is None or computed.expected is None:
        return None
    if computed.expected and abs(float(computed.student - computed.expected)) / max(abs(float(computed.expected)), 1.0) > 1.0:
        return _tag(
            ErrorCode.NO_CHECKING,
            0.52,
            "学生答案与合理结果差距超过一倍，若有估算或验算通常能发现。",
            "训练先估算范围，再用逆运算或代入检查。",
            "算完先问自己：这个答案和题目里的数比起来合理吗？",
        )
    return None


def _extract_expression(problem: str) -> str | None:
    text = _normalize_math_text(problem)
    before_equal = text.split("=")[0]
    match = re.search(r"[\d\s+\-*/().]+", before_equal)
    if not match:
        return None
    expression = match.group(0).strip()
    if not expression or not _EXPR_RE.match(expression):
        return None
    if not any(op in expression for op in ["+", "-", "*", "/"]):
        return None
    return expression


def _parse_number(value: str) -> Fraction | None:
    fraction_match = re.search(r"\d+\s*/\s*\d+", str(value))
    if fraction_match:
        numerator, denominator = fraction_match.group(0).split("/")
        try:
            return Fraction(int(numerator.strip()), int(denominator.strip()))
        except (ValueError, ZeroDivisionError):
            return None
    match = _DIGIT_RE.search(str(value))
    if not match:
        return None
    try:
        return Fraction(match.group(0))
    except ValueError:
        return None


def _integer_numbers(expression: str) -> list[int]:
    return [int(n) for n in re.findall(r"\d+", expression) if "." not in n]


def _normalize_math_text(text: str) -> str:
    return (
        text.replace("×", "*")
        .replace("÷", "/")
        .replace(" x ", " * ")
        .replace(" X ", " * ")
        .replace("＝", "=")
        .replace("—", "-")
    )


def _needs_borrow(a: int, b: int) -> bool:
    while a or b:
        if a % 10 < b % 10:
            return True
        a //= 10
        b //= 10
    return False


def _needs_carry(a: int, b: int) -> bool:
    while a or b:
        if a % 10 + b % 10 >= 10:
            return True
        a //= 10
        b //= 10
    return False


def _subtract_without_borrow(a: int, b: int) -> int:
    place = 1
    result = 0
    while a or b:
        result += abs((a % 10) - (b % 10)) * place
        a //= 10
        b //= 10
        place *= 10
    return result


def _add_without_carry(a: int, b: int) -> int:
    place = 1
    result = 0
    while a or b:
        result += ((a % 10 + b % 10) % 10) * place
        a //= 10
        b //= 10
        place *= 10
    return result


def _eval_left_to_right(expression: str) -> Fraction | None:
    tokens = re.findall(r"\d+(?:\.\d+)?|[+\-*/]", expression)
    if not tokens:
        return None
    try:
        value = Fraction(tokens[0])
        index = 1
        ops = {
            "+": operator.add,
            "-": operator.sub,
            "*": operator.mul,
            "/": operator.truediv,
        }
        while index < len(tokens) - 1:
            value = ops[tokens[index]](value, Fraction(tokens[index + 1]))
            index += 2
        return value
    except (KeyError, ValueError, ZeroDivisionError):
        return None


def _eval_expression(expression: str) -> Fraction | None:
    try:
        node = ast.parse(expression, mode="eval")
        return _eval_ast(node.body)
    except (SyntaxError, ValueError, ZeroDivisionError):
        return None


def _eval_ast(node: ast.AST) -> Fraction:
    if isinstance(node, ast.Constant) and isinstance(node.value, int | float):
        return Fraction(str(node.value))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_eval_ast(node.operand)
    if isinstance(node, ast.BinOp):
        left = _eval_ast(node.left)
        right = _eval_ast(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
    raise ValueError("unsupported expression")


def infer_expected_from_problem(problem: str) -> Fraction | None:
    expression = _extract_expression(problem)
    return _eval_expression(expression) if expression else None


def _tag(
    code: ErrorCode,
    confidence: float,
    evidence: str,
    teacher_action: str,
    student_feedback: str,
) -> ErrorTag:
    return ErrorTag(
        code=code,
        label=ERROR_LABELS[code],
        confidence=confidence,
        evidence=evidence,
        teacher_action=teacher_action,
        student_feedback=student_feedback,
    )


def _fraction_to_json(value: Fraction | None) -> str | None:
    if value is None:
        return None
    if value.denominator == 1:
        return str(value.numerator)
    return str(float(value))
