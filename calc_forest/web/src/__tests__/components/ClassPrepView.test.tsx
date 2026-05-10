import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ClassPrepView } from "@/components/classroom/ClassPrepView";
import type { ClassForestResponse, StudentTree } from "@/lib/types";

vi.mock("@/lib/api", () => ({
  generateQuiz: vi.fn().mockResolvedValue({
    quiz_id: "quiz-123",
    problem_count: 5,
    error_codes_target: ["E02"],
  }),
  getQuiz: vi.fn().mockResolvedValue({
    quiz_id: "quiz-123",
    class_id: "C001",
    title: "随堂练习",
    status: "active",
    target_error_codes: ["E02"],
    difficulty: "B",
    problems: [
      {
        sequence: 1,
        problem: "3.6 × 2.5",
        correct_answer: "9",
        target_error_code: "E02",
        difficulty: "B",
        knowledge_point: "小数乘法",
        hint: "先按整数乘法算",
      },
    ],
    created_at: "2026-05-10",
  }),
}));

function makeTree(id: string, name: string, errors: string[]): StudentTree {
  return {
    student_id: id,
    student_name: name,
    tree_species_id: "cherry",
    tree_species_emoji: "🌸",
    tree_species_name: "樱花树",
    current_stage: "taller",
    days_completed: 10,
    total_days: 30,
    overall_accuracy: 0.75,
    weekly_accuracy: [
      { week_number: 1, accuracy: 0.7, total_attempts: 10, correct_count: 7 },
    ],
    dominant_errors: errors,
    total_attempts: 10,
    correct_count: 7,
    emotional_state: "happy",
    emotional_intensity: 0.3,
    encouragement_needed: false,
  };
}

const mockForest: ClassForestResponse = {
  class_id: "C001",
  class_name: "六年级一班",
  grade: 6,
  semester: "下册",
  academic_year: "2025-2026",
  cycle_id: "cycle-1",
  week_number: 3,
  trees: [
    makeTree("S001", "小明", ["E02", "E03"]),
    makeTree("S002", "小红", ["E02"]),
    makeTree("S003", "小刚", ["E03"]),
  ],
  class_accuracy: 0.78,
  class_top_errors: ["E02", "E03"],
  class_emotional_state: "happy",
};

describe("ClassPrepView", () => {
  it("renders class name in header", () => {
    render(<ClassPrepView forest={mockForest} onStartQuiz={() => {}} />);
    expect(screen.getByText(/六年级一班/)).toBeInTheDocument();
  });

  it("renders classroom mode heading", () => {
    render(<ClassPrepView forest={mockForest} onStartQuiz={() => {}} />);
    expect(screen.getByText(/课堂模式/)).toBeInTheDocument();
  });

  it("renders class accuracy percentage", () => {
    render(<ClassPrepView forest={mockForest} onStartQuiz={() => {}} />);
    expect(screen.getByText("78%")).toBeInTheDocument();
  });

  it("renders error analysis section heading", () => {
    render(<ClassPrepView forest={mockForest} onStartQuiz={() => {}} />);
    expect(screen.getByText("班级错因画像")).toBeInTheDocument();
  });

  it("renders top error codes from class data", () => {
    render(<ClassPrepView forest={mockForest} onStartQuiz={() => {}} />);
    expect(screen.getByText("高频错因")).toBeInTheDocument();
    expect(screen.getAllByText("进位错误").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("退位错误").length).toBeGreaterThanOrEqual(1);
  });

  it("renders student count", () => {
    render(<ClassPrepView forest={mockForest} onStartQuiz={() => {}} />);
    expect(screen.getByText("3 名学生")).toBeInTheDocument();
  });

  it("renders quiz configuration section", () => {
    render(<ClassPrepView forest={mockForest} onStartQuiz={() => {}} />);
    expect(screen.getByText("随堂测验配置")).toBeInTheDocument();
  });

  it("renders difficulty buttons (基础, 中等, 挑战)", () => {
    render(<ClassPrepView forest={mockForest} onStartQuiz={() => {}} />);
    expect(screen.getByText("🌱 基础")).toBeInTheDocument();
    expect(screen.getByText("🌿 中等")).toBeInTheDocument();
    expect(screen.getByText("🌳 挑战")).toBeInTheDocument();
  });

  it("renders generate quiz button", () => {
    render(<ClassPrepView forest={mockForest} onStartQuiz={() => {}} />);
    expect(screen.getByText("✨ 生成随堂练习")).toBeInTheDocument();
  });

  it("renders teaching tips section", () => {
    render(<ClassPrepView forest={mockForest} onStartQuiz={() => {}} />);
    expect(screen.getByText("教学建议")).toBeInTheDocument();
  });

  it("renders class emotional state label", () => {
    render(<ClassPrepView forest={mockForest} onStartQuiz={() => {}} />);
    expect(screen.getByText(/状态良好/)).toBeInTheDocument();
  });

  it("renders error code selection buttons for all error codes", () => {
    render(<ClassPrepView forest={mockForest} onStartQuiz={() => {}} />);
    expect(screen.getByText("目标错因")).toBeInTheDocument();
  });

  it("renders problem count selector", () => {
    render(<ClassPrepView forest={mockForest} onStartQuiz={() => {}} />);
    expect(screen.getByText("题数")).toBeInTheDocument();
  });
});
