from __future__ import annotations

import json
import io
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from zipfile import ZipFile

import mammoth
from PIL import Image
from rapidocr_onnxruntime import RapidOCR


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT.parent.parent / "research" / "teacher_feedback_curated"
PER_FILE_DIR = OUTPUT_DIR / "by_source"
SUMMARY_PATH = OUTPUT_DIR / "teacher_feedback_master_digest.md"
MANIFEST_PATH = OUTPUT_DIR / "manifest.json"


SOURCE_ORDER = [
    "计算小树苗设计资料.docx",
    "第4次修改（5月2号）.docx",
    "计算练习出题原则和具体措施.docx",
    "2025春学期教学进度计划.docx",
    "人教版六年级上册数学整理资料.docx",
]

TOPIC_BUCKETS = {
    "产品定位与教学目标": [
        "长期", "森林", "成长", "坚持", "教师", "孩子", "温和", "陪伴", "定位", "目标", "起点",
    ],
    "诊断与练习设计原则": [
        "诊断", "错因", "练习", "出题", "计算", "纠错", "讲评", "复现", "正确率", "引导", "方法",
    ],
    "森林与激励机制": [
        "树", "树种", "鼓励", "激励", "森林", "成长", "小树苗", "荣誉", "兴趣",
    ],
    "教材与学期进度": [
        "教材", "人教版", "六年级", "上册", "下册", "周次", "进度", "单元", "学期", "复习",
    ],
    "比赛申报可复用表述": [
        "AI", "教师端", "减负", "智能", "个性化", "精准", "课堂", "作业", "评价", "系统",
    ],
}


@dataclass
class ImageNote:
    name: str
    ocr_text: str
    review_status: str
    note: str


@dataclass
class SourceDigest:
    source_name: str
    source_path: Path
    html_text: str
    paragraphs: list[str]
    image_notes: list[ImageNote]
    curated_summary: str
    trace_points: list[str]


def slugify(name: str) -> str:
    stem = Path(name).stem
    slug = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "-", stem).strip("-")
    return slug or "teacher-feedback"


def clean_text(text: str) -> str:
    text = text.replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def split_paragraphs(text: str) -> list[str]:
    parts = [clean_text(part) for part in re.split(r"\n{2,}", text)]
    return [part for part in parts if part]


def extract_docx_text(docx_path: Path) -> tuple[str, list[str]]:
    with open(docx_path, "rb") as fh:
        result = mammoth.extract_raw_text(fh)
    text = clean_text(result.value)
    return text, split_paragraphs(text)


def iter_docx_images(docx_path: Path) -> Iterable[tuple[str, bytes]]:
    with ZipFile(docx_path) as zf:
        for name in sorted(zf.namelist()):
            if name.startswith("word/media/") and not name.endswith("/"):
                yield Path(name).name, zf.read(name)


def run_ocr(docx_path: Path, engine: RapidOCR) -> list[ImageNote]:
    notes: list[ImageNote] = []
    for image_name, image_bytes in iter_docx_images(docx_path):
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            result, _ = engine(image)
            lines = []
            if result:
                for item in result:
                    if len(item) >= 2 and isinstance(item[1], str):
                        lines.append(item[1].strip())
            ocr_text = clean_text("\n".join(line for line in lines if line))
            if not ocr_text:
                ocr_text = "未稳定识别出可用文字"
                review_status = "needs_manual_review"
                note = "图片已抽取，但 OCR 结果为空，需要人工查看原图。"
            else:
                review_status = "ocr_extracted_needs_review"
                note = "OCR 已自动抽取，数学表达、教材术语和编号需人工复核。"
        except Exception as exc:
            ocr_text = "OCR 失败"
            review_status = "ocr_failed"
            note = f"OCR 执行失败：{exc}"
        notes.append(
            ImageNote(
                name=image_name,
                ocr_text=ocr_text,
                review_status=review_status,
                note=note,
            )
        )
    return notes


def select_trace_points(paragraphs: list[str]) -> list[str]:
    traces = []
    for paragraph in paragraphs:
        if any(keyword in paragraph for keyword in ["必须", "不", "应", "支持", "练习", "教师", "成长", "教材", "进度"]):
            traces.append(paragraph)
        if len(traces) >= 8:
            break
    return traces or paragraphs[:5]


def build_curated_summary(source_name: str, paragraphs: list[str], image_notes: list[ImageNote]) -> str:
    joined = "\n".join(paragraphs[:18])
    image_hint = ""
    if image_notes:
        image_hint = "该文档含嵌入图片/截图，已将 OCR 信息并入整理结论并标注待复核项。"

    if source_name == "计算小树苗设计资料.docx":
        return (
            "这份材料更像项目概念母本，核心在于把计算训练从一次性作业转成长期成长体验。"
            "它强调“森林”而不是单棵树，强调从任何起点开始都有效，产品气质应偏温和陪伴而非竞争驱动。"
            "对当前项目最有价值的不是完整功能清单，而是三条原则：坚持短时练习、把错误处理成可被引导的成长节点、让教师与学生都能感到负担轻。"
            f"{image_hint}"
        )
    if source_name == "第4次修改（5月2号）.docx":
        return (
            "这份修订稿强化了教师视角下的落地约束。材料持续把 AI 放在“辅助教师诊断、讲评、出题”的位置，"
            "避免把系统写成自动替代教师的批改器；同时把森林成长、树种选择、多模态输入视为值得保留的方向，但不要求这些方向在 MVP 阶段全部重工程实现。"
            f"{image_hint}"
        )
    if source_name == "计算练习出题原则和具体措施.docx":
        return (
            "这份文档是最直接的练习生成规则来源。它明确要求学什么练什么、只练计算、不超前出题，并给出课内、课后、周末的时长与题量边界。"
            "同时，它把错误复现、按正确率分层、非计算周滚动旧计算写成了操作规则，因此后续练习系统应优先体现进度约束与错题回放，而不是追求泛题型扩张。"
        )
    if source_name == "2025春学期教学进度计划.docx":
        return (
            "这份教学进度计划提供了把练习系统与真实学期节奏对齐的样板。"
            "它的价值不在于某一学期计划本身，而在于明确了周次、单元、节假日与练习节奏之间存在强关联，"
            "因此未来任何自动练习推荐都不应脱离“当前教到哪里”这个前置条件。"
        )
    if source_name == "人教版六年级上册数学整理资料.docx":
        return (
            "这份资料是最重的上游知识源，包含大量教材整理、知识点与图片化内容。"
            "它适合作为后续知识库与教材约束的基础材料，而不适合直接拿来当产品文案。"
            "当前整理应优先提炼教材结构、计算知识点、分层练习提示和方法表达，同时对截图内容执行 OCR 并保留人工复核痕迹。"
        )
    return joined[:400]


def build_topic_sections(digests: list[SourceDigest]) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = defaultdict(list)
    for digest in digests:
        combined = digest.paragraphs + [note.ocr_text for note in digest.image_notes if note.ocr_text]
        for topic, keywords in TOPIC_BUCKETS.items():
            matches = []
            for paragraph in combined:
                if any(keyword in paragraph for keyword in keywords):
                    matches.append(paragraph)
                if len(matches) >= 4:
                    break
            if matches:
                sections[topic].append(
                    f"来源：`{digest.source_name}`。"
                    + " ".join(matches[:3])
                )
    return sections


def write_source_digest(digest: SourceDigest) -> None:
    PER_FILE_DIR.mkdir(parents=True, exist_ok=True)
    target = PER_FILE_DIR / f"{slugify(digest.source_name)}.md"
    lines = [
        f"# {Path(digest.source_name).stem}",
        "",
        "## 来源",
        "",
        f"- 原始文件：`docs/source_materials/teacher_feedback/{digest.source_name}`",
        f"- 整理方式：正文抽取 + 图片 OCR + 人工复核提示",
        "",
        "## 高度整理结论",
        "",
        digest.curated_summary,
        "",
        "## 关键可追溯信息",
        "",
    ]
    for trace in digest.trace_points:
        lines.append(f"- {trace}")
    lines.extend([
        "",
        "## 图片 OCR 与复核记录",
        "",
    ])
    if digest.image_notes:
        for note in digest.image_notes:
            lines.append(f"### {note.name}")
            lines.append("")
            lines.append(f"- `review_status`: `{note.review_status}`")
            lines.append(f"- 复核说明：{note.note}")
            lines.append("- OCR 文本：")
            lines.append("")
            lines.append("```text")
            lines.append(note.ocr_text)
            lines.append("```")
            lines.append("")
    else:
        lines.append("- 无嵌入图片。")
        lines.append("")

    lines.extend([
        "## 正文抽取",
        "",
        "```text",
        digest.html_text,
        "```",
        "",
    ])
    target.write_text("\n".join(lines), encoding="utf-8")


def write_master_digest(digests: list[SourceDigest]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    sections = build_topic_sections(digests)
    lines = [
        "# 教师反馈材料主题整理稿",
        "",
        "> 基于 `docs/source_materials/teacher_feedback/` 中 5 份原始 Word 材料重新整理。",
        "> 本稿目标是作为后续规格、知识库与比赛材料的可复用资产；结论做了高度改写，但每条核心判断都保留来源线索。",
        "",
        "## 来源范围",
        "",
    ]
    for digest in digests:
        lines.append(f"- `docs/source_materials/teacher_feedback/{digest.source_name}`")
    lines.extend([
        "",
        "## 一、产品定位与教学目标",
        "",
        "“我的计算森林”不应被定义成会判对错的自动批改器，而应被定义成帮助教师快速看见计算问题、帮助孩子在低压力中形成长期练习节奏的教学辅助系统。"
        "教师始终是主导者，AI 的价值在于压缩诊断、讲评、出题和整理信息的时间，而不是替代教学判断。",
        "",
        "关键证据：",
    ])
    for item in sections.get("产品定位与教学目标", []):
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## 二、诊断与练习设计原则",
        "",
        "教师材料最清晰的一条主线是：学什么，练什么；没教到的不练；没有新计算内容时就滚动旧计算；练习保持短时、计算型、可复现错题。"
        "这意味着后续系统的练习推荐逻辑应优先受教学进度、近期正确率、近期错误类型约束，而不是做开放式题库生成。",
        "",
        "关键证据：",
    ])
    for item in sections.get("诊断与练习设计原则", []):
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## 三、森林、树种与激励机制",
        "",
        "森林隐喻应继续保留，但它更适合作为温和的持续反馈层，而不是独立的重游戏化系统。"
        "树种选择、成长鼓励、森林积累这些元素的价值，在于让孩子拥有自我投射与兴趣入口，同时避免排名、打卡压力和外部比较。",
        "",
        "关键证据：",
    ])
    for item in sections.get("森林与激励机制", []):
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## 四、教材与学期进度",
        "",
        "学期进度与教材结构不是背景信息，而是后续练习系统的硬约束。"
        "六年级上册整理资料与教学进度计划共同说明，系统至少需要理解教材版本、年级、单元、周次以及哪些周属于非计算主题，才能避免出题脱节。",
        "",
        "关键证据：",
    ])
    for item in sections.get("教材与学期进度", []):
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## 五、比赛申报可复用表述",
        "",
        "对外材料里最值得复用的口径，是“教师端减负、课堂诊断更快、练习生成更贴近教学进度、孩子得到温和而非压力式的成长反馈”。"
        "不宜把 OCR、全自动拍照批改、完整学生端或六年完整森林系统写成当前已经交付的能力。",
        "",
        "关键证据：",
    ])
    for item in sections.get("比赛申报可复用表述", []):
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## 六、建议替代关系",
        "",
        "- 当前总整理稿可作为 `docs/specs/teacher_feedback_digest.md` 的上游增强版参考。",
        "- 逐文件整理稿适合后续继续沉淀到知识库、规格文档或比赛答辩材料中。",
        "- 对于图片 OCR 结果，仍需以人工复核为准，尤其是教材术语、数学表达与编号。",
        "",
    ])
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PER_FILE_DIR.mkdir(parents=True, exist_ok=True)
    engine = RapidOCR()
    digests: list[SourceDigest] = []

    for file_name in SOURCE_ORDER:
        source_path = ROOT / file_name
        text, paragraphs = extract_docx_text(source_path)
        image_notes = run_ocr(source_path, engine)
        digest = SourceDigest(
            source_name=file_name,
            source_path=source_path,
            html_text=text,
            paragraphs=paragraphs,
            image_notes=image_notes,
            curated_summary=build_curated_summary(file_name, paragraphs, image_notes),
            trace_points=select_trace_points(paragraphs),
        )
        write_source_digest(digest)
        digests.append(digest)

    write_master_digest(digests)

    manifest = {
        "sources": [
            {
                "source_name": digest.source_name,
                "source_relpath": str(digest.source_path.relative_to(ROOT.parent.parent.parent)),
                "per_source_markdown": str((PER_FILE_DIR / f"{slugify(digest.source_name)}.md").relative_to(ROOT.parent.parent.parent)),
                "image_count": len(digest.image_notes),
                "ocr_review_statuses": [note.review_status for note in digest.image_notes],
            }
            for digest in digests
        ],
        "master_digest": str(SUMMARY_PATH.relative_to(ROOT.parent.parent.parent)),
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
