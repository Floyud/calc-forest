import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { QuizSummaryView } from "@/components/classroom/QuizSummaryView";
import type { QuizProblemItem } from "@/lib/types";

const mockProblems: QuizProblemItem[] = [
  {
    sequence: 1,
    problem: "3.6 × 2.5",
    correct_answer: "9",
    target_error_code: "E02",
    difficulty: "B",
    knowledge_point: "小数乘法",
    hint: "先按整数乘法算，再数小数位数",
  },
  {
    sequence: 2,
    problem: "402 - 178",
    correct_answer: "224",
    target_error_code: "E03",
    difficulty: "A",
    knowledge_point: "退位减法",
    hint: "个位不够减要借位",
  },
  {
    sequence: 3,
    problem: "125 × 32",
    correct_answer: "4000",
    target_error_code: null,
    difficulty: "B",
    knowledge_point: "简便运算",
    hint: "32可以拆成4×8",
  },
];

const mockResponses = [
  { sequence: 1, response: "mostly_correct" },
  { sequence: 2, response: "mostly_wrong" },
  { sequence: 3, response: "mixed" },
];

describe("QuizSummaryView", () => {
  it("renders mood header based on results", () => {
    render(
      <QuizSummaryView
        problems={mockProblems}
        responses={mockResponses}
        onBack={() => {}}
        onNewQuiz={() => {}}
      />,
    );
    expect(screen.getByText("找到薄弱点了")).toBeInTheDocument();
  });

  it("shows error distribution section", () => {
    render(
      <QuizSummaryView
        problems={mockProblems}
        responses={mockResponses}
        onBack={() => {}}
        onNewQuiz={() => {}}
      />,
    );
    expect(screen.getByText("错因分布")).toBeInTheDocument();
  });

  it("displays per-problem feedback section", () => {
    render(
      <QuizSummaryView
        problems={mockProblems}
        responses={mockResponses}
        onBack={() => {}}
        onNewQuiz={() => {}}
      />,
    );
    expect(screen.getByText("逐题反馈")).toBeInTheDocument();
  });

  it("shows stat values (correct, mixed, wrong counts)", () => {
    render(
      <QuizSummaryView
        problems={mockProblems}
        responses={mockResponses}
        onBack={() => {}}
        onNewQuiz={() => {}}
      />,
    );
    expect(screen.getByText("课堂掌握率")).toBeInTheDocument();
  });

  it("renders action buttons", () => {
    render(
      <QuizSummaryView
        problems={mockProblems}
        responses={mockResponses}
        onBack={() => {}}
        onNewQuiz={() => {}}
      />,
    );
    expect(
      screen.getByRole("button", { name: /返回准备/ }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /再来一组/ }),
    ).toBeInTheDocument();
  });
});
