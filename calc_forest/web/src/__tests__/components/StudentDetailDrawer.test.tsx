import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { StudentDetailDrawer } from "@/components/forest/StudentDetailDrawer";
import type { StudentTree } from "@/lib/types";

vi.mock("@/components/forest/trees/SvgTree", () => ({
  SvgTree: () => null,
}));
vi.mock("@/lib/api/hooks", () => ({
  useUpdateStudentProfile: () => ({
    mutate: vi.fn(),
    isPending: false,
  }),
}));

const mockTree: StudentTree = {
  student_id: "S001",
  student_name: "小明",
  tree_species_id: "cherry",
  tree_species_emoji: "🌸",
  tree_species_name: "樱花树",
  current_stage: "taller",
  days_completed: 18,
  total_days: 30,
  overall_accuracy: 0.85,
  weekly_accuracy: [
    { week_number: 1, accuracy: 0.7, total_attempts: 10, correct_count: 7 },
    { week_number: 2, accuracy: 0.8, total_attempts: 10, correct_count: 8 },
    { week_number: 3, accuracy: 0.85, total_attempts: 10, correct_count: 9 },
  ],
  dominant_errors: ["E02", "E03"],
  total_attempts: 30,
  correct_count: 25,
  emotional_state: "happy",
  emotional_intensity: 0.5,
  encouragement_needed: false,
};

describe("StudentDetailDrawer", () => {
  it("renders student name when tree is provided", () => {
    render(<StudentDetailDrawer tree={mockTree} onClose={() => {}} />);
    expect(screen.getByText("小明")).toBeInTheDocument();
  });

  it("renders tab buttons", () => {
    render(<StudentDetailDrawer tree={mockTree} onClose={() => {}} />);
    expect(
      screen.getByRole("button", { name: "数据概览" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "错因轨迹" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "学习画像" }),
    ).toBeInTheDocument();
  });

  it("shows overview tab content by default", () => {
    render(<StudentDetailDrawer tree={mockTree} onClose={() => {}} />);
    expect(screen.getByText("总准确率")).toBeInTheDocument();
  });

  it("switches to trajectory tab on click", async () => {
    const user = userEvent.setup();
    render(<StudentDetailDrawer tree={mockTree} onClose={() => {}} />);
    await user.click(screen.getByRole("button", { name: "错因轨迹" }));
    expect(screen.getByText("错因时间线")).toBeInTheDocument();
  });

  it("renders close button", () => {
    render(<StudentDetailDrawer tree={mockTree} onClose={() => {}} />);
    expect(
      screen.getByRole("button", { name: "关闭详情" }),
    ).toBeInTheDocument();
  });
});
