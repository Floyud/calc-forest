import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { StudentTreeCard } from "@/components/forest/StudentTreeCard";
import type { StudentTree } from "@/lib/types";

vi.mock("@/components/forest/canvas/CanvasTreeCard", () => ({
  CanvasTree: () => null,
}));

vi.mock("@/components/forest/trees/SvgTree", () => ({
  SvgTree: () => null,
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

describe("StudentTreeCard", () => {
  it("renders student name", () => {
    render(
      <StudentTreeCard
        tree={mockTree}
        onClick={() => {}}
        index={0}
        useCanvas={false}
      />,
    );
    expect(screen.getByText("小明")).toBeInTheDocument();
  });

  it("displays accuracy percentage", () => {
    render(
      <StudentTreeCard
        tree={mockTree}
        onClick={() => {}}
        index={0}
        useCanvas={false}
      />,
    );
    expect(screen.getByText("85%")).toBeInTheDocument();
  });

  it("renders emotion badge with label", () => {
    render(
      <StudentTreeCard
        tree={mockTree}
        onClick={() => {}}
        index={0}
        useCanvas={false}
      />,
    );
    expect(screen.getByText(/开心成长/)).toBeInTheDocument();
  });

  it("shows correct/total attempt count", () => {
    render(
      <StudentTreeCard
        tree={mockTree}
        onClick={() => {}}
        index={0}
        useCanvas={false}
      />,
    );
    expect(screen.getByText("25/30 题")).toBeInTheDocument();
  });

  it("renders as a button with aria-label containing student name", () => {
    render(
      <StudentTreeCard
        tree={mockTree}
        onClick={() => {}}
        index={0}
        useCanvas={false}
      />,
    );
    expect(
      screen.getByRole("button", { name: /小明/ }),
    ).toBeInTheDocument();
  });
});
