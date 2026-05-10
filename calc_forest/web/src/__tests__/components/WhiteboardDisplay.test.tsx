import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { WhiteboardDisplay } from "@/components/classroom/WhiteboardDisplay";
import type { QuizProblemItem } from "@/lib/types";

vi.mock("@/lib/api", () => ({
  recordQuizResponse: vi.fn().mockResolvedValue({ ok: true }),
}));

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
];

describe("WhiteboardDisplay", () => {
  it("renders the problem text", () => {
    render(
      <WhiteboardDisplay
        problems={mockProblems}
        quizId="quiz-1"
        onExit={() => {}}
        onComplete={() => {}}
      />,
    );
    expect(screen.getByText("3.6 × 2.5")).toBeInTheDocument();
  });

  it("renders problem counter showing current/total", () => {
    render(
      <WhiteboardDisplay
        problems={mockProblems}
        quizId="quiz-1"
        onExit={() => {}}
        onComplete={() => {}}
      />,
    );
    expect(screen.getByText("1 / 2")).toBeInTheDocument();
  });

  it("renders error code badge for targeted problem", () => {
    render(
      <WhiteboardDisplay
        problems={mockProblems}
        quizId="quiz-1"
        onExit={() => {}}
        onComplete={() => {}}
      />,
    );
    expect(screen.getByText(/E02/)).toBeInTheDocument();
  });

  it("renders the hint button in showing_problem step", () => {
    render(
      <WhiteboardDisplay
        problems={mockProblems}
        quizId="quiz-1"
        onExit={() => {}}
        onComplete={() => {}}
      />,
    );
    expect(screen.getByText("💡 提示")).toBeInTheDocument();
  });

  it("reveals the hint when hint button is clicked", async () => {
    const user = userEvent.setup();
    render(
      <WhiteboardDisplay
        problems={mockProblems}
        quizId="quiz-1"
        onExit={() => {}}
        onComplete={() => {}}
      />,
    );
    await user.click(screen.getByText("💡 提示"));
    expect(screen.getByText("先按整数乘法算，再数小数位数")).toBeInTheDocument();
  });

  it("reveals the answer when answer button is clicked", async () => {
    const user = userEvent.setup();
    render(
      <WhiteboardDisplay
        problems={mockProblems}
        quizId="quiz-1"
        onExit={() => {}}
        onComplete={() => {}}
      />,
    );
    await user.click(screen.getByText("💡 提示"));
    await user.click(screen.getByText("✨ 答案"));
    expect(screen.getByText("9")).toBeInTheDocument();
  });

  it("renders response buttons after answer is revealed", async () => {
    const user = userEvent.setup();
    render(
      <WhiteboardDisplay
        problems={mockProblems}
        quizId="quiz-1"
        onExit={() => {}}
        onComplete={() => {}}
      />,
    );
    await user.click(screen.getByText("💡 提示"));
    await user.click(screen.getByText("✨ 答案"));
    expect(screen.getByText("多数对了")).toBeInTheDocument();
    expect(screen.getByText("一半一半")).toBeInTheDocument();
    expect(screen.getByText("需要再练")).toBeInTheDocument();
  });

  it("shows keyboard shortcut hints on response buttons", async () => {
    const user = userEvent.setup();
    render(
      <WhiteboardDisplay
        problems={mockProblems}
        quizId="quiz-1"
        onExit={() => {}}
        onComplete={() => {}}
      />,
    );
    await user.click(screen.getByText("💡 提示"));
    await user.click(screen.getByText("✨ 答案"));
    expect(screen.getByText("按 1")).toBeInTheDocument();
    expect(screen.getByText("按 2")).toBeInTheDocument();
    expect(screen.getByText("按 3")).toBeInTheDocument();
  });

  it("renders exit button", () => {
    render(
      <WhiteboardDisplay
        problems={mockProblems}
        quizId="quiz-1"
        onExit={() => {}}
        onComplete={() => {}}
      />,
    );
    expect(screen.getByText("退出")).toBeInTheDocument();
  });

  it("renders ESC hint in control bar", () => {
    render(
      <WhiteboardDisplay
        problems={mockProblems}
        quizId="quiz-1"
        onExit={() => {}}
        onComplete={() => {}}
      />,
    );
    expect(screen.getByText("ESC 退出")).toBeInTheDocument();
  });
});
