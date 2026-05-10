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

const treeNeedingCare: StudentTree = {
  student_id: "S002",
  student_name: "小红",
  tree_species_id: "oak",
  tree_species_emoji: "🌳",
  tree_species_name: "橡树",
  current_stage: "sprout",
  days_completed: 5,
  total_days: 30,
  overall_accuracy: 0.42,
  weekly_accuracy: [
    { week_number: 1, accuracy: 0.5, total_attempts: 10, correct_count: 5 },
    { week_number: 2, accuracy: 0.4, total_attempts: 10, correct_count: 4 },
  ],
  dominant_errors: ["E03", "E05"],
  total_attempts: 20,
  correct_count: 8,
  emotional_state: "struggling",
  emotional_intensity: 0.8,
  encouragement_needed: true,
};

describe("StudentTreeCard (expanded)", () => {
  it("shows '需要关怀' badge when encouragement_needed is true", () => {
    render(
      <StudentTreeCard
        tree={treeNeedingCare}
        onClick={() => {}}
        index={0}
        useCanvas={false}
      />,
    );
    expect(screen.getByText("需要关怀")).toBeInTheDocument();
  });

  it("does not show '需要关怀' when encouragement_needed is false", () => {
    const tree = { ...treeNeedingCare, encouragement_needed: false };
    render(
      <StudentTreeCard
        tree={tree}
        onClick={() => {}}
        index={0}
        useCanvas={false}
      />,
    );
    expect(screen.queryByText("需要关怀")).not.toBeInTheDocument();
  });

  it("shows dominant error codes", () => {
    render(
      <StudentTreeCard
        tree={treeNeedingCare}
        onClick={() => {}}
        index={0}
        useCanvas={false}
      />,
    );
    expect(screen.getByText("E03")).toBeInTheDocument();
    expect(screen.getByText("E05")).toBeInTheDocument();
  });

  it("limits dominant errors shown to first 2", () => {
    const treeWithManyErrors: StudentTree = {
      ...treeNeedingCare,
      dominant_errors: ["E01", "E02", "E03", "E04"],
    };
    render(
      <StudentTreeCard
        tree={treeWithManyErrors}
        onClick={() => {}}
        index={0}
        useCanvas={false}
      />,
    );
    expect(screen.getByText("E01")).toBeInTheDocument();
    expect(screen.getByText("E02")).toBeInTheDocument();
    expect(screen.queryByText("E03")).not.toBeInTheDocument();
    expect(screen.queryByText("E04")).not.toBeInTheDocument();
  });

  it("renders progress bar with correct width based on accuracy", () => {
    const { container } = render(
      <StudentTreeCard
        tree={treeNeedingCare}
        onClick={() => {}}
        index={0}
        useCanvas={false}
      />,
    );
    const progressBar = container.querySelector("[style*='width: 42%']");
    expect(progressBar).toBeInTheDocument();
  });

  it("hides emotion badge in compact mode", () => {
    render(
      <StudentTreeCard
        tree={treeNeedingCare}
        onClick={() => {}}
        index={0}
        useCanvas={false}
        compact
      />,
    );
    expect(screen.queryByText(/需要关注/)).not.toBeInTheDocument();
  });

  it("hides dominant errors in compact mode", () => {
    render(
      <StudentTreeCard
        tree={treeNeedingCare}
        onClick={() => {}}
        index={0}
        useCanvas={false}
        compact
      />,
    );
    expect(screen.queryByText("E03")).not.toBeInTheDocument();
    expect(screen.queryByText("E05")).not.toBeInTheDocument();
  });

  it("hides '需要关怀' badge in compact mode", () => {
    render(
      <StudentTreeCard
        tree={treeNeedingCare}
        onClick={() => {}}
        index={0}
        useCanvas={false}
        compact
      />,
    );
    expect(screen.queryByText("需要关怀")).not.toBeInTheDocument();
  });

  it("shows accuracy percentage even in compact mode", () => {
    render(
      <StudentTreeCard
        tree={treeNeedingCare}
        onClick={() => {}}
        index={0}
        useCanvas={false}
        compact
      />,
    );
    expect(screen.getByText("42%")).toBeInTheDocument();
  });
});
