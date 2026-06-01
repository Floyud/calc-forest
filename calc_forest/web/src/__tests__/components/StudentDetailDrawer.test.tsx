import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
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
vi.mock("@/lib/api", () => ({
  getStudentProfile: vi.fn().mockResolvedValue({
    accuracy_by_error_code: { E02: 0.8, E03: 0.65 },
    total_attempts: 30,
    weak_knowledge_points: ["退位减法"],
    student: {
      personality_tags: [],
      learning_style: "",
      notes: "",
      guidance_mode: "standard",
    },
  }),
  getStudentMastery: vi.fn().mockResolvedValue({
    error_codes: {
      E02: { mastery_probability: 0.78, zone: "developing", total_attempts: 10, correct_count: 8 },
      E03: { mastery_probability: 0.62, zone: "watch", total_attempts: 8, correct_count: 5 },
    },
    overall_mastery: 0.7,
    mastered_count: 0,
    total_error_codes: 2,
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
  function renderDrawer() {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });
    return render(
      <QueryClientProvider client={queryClient}>
        <StudentDetailDrawer tree={mockTree} onClose={() => {}} />
      </QueryClientProvider>,
    );
  }

  it("renders student name when tree is provided", () => {
    renderDrawer();
    expect(screen.getByText("小明")).toBeInTheDocument();
  });

  it("renders tab buttons", () => {
    renderDrawer();
    expect(
      screen.getByRole("tab", { name: "数据概览" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("tab", { name: "错因轨迹" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("tab", { name: "学习画像" }),
    ).toBeInTheDocument();
  });

  it("shows overview tab content by default", () => {
    renderDrawer();
    expect(screen.getByText("总准确率")).toBeInTheDocument();
  });

  it("exposes trajectory tab for switching", () => {
    renderDrawer();
    expect(screen.getByRole("tab", { name: "错因轨迹" })).toBeInTheDocument();
  });

  it("renders close button", () => {
    renderDrawer();
    expect(
      screen.getByRole("button", { name: "关闭详情" }),
    ).toBeInTheDocument();
  });
});
