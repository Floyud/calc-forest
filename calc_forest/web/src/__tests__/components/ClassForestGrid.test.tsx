import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { ClassForestGrid } from "@/components/forest/ClassForestGrid";
import type { ClassForestResponse, StudentTree } from "@/lib/types";

vi.mock("@/components/forest/canvas/CanvasTreeCard", () => ({
  CanvasTree: () => null,
}));
vi.mock("@/components/forest/trees/SvgTree", () => ({
  SvgTree: () => null,
}));

function makeTree(id: string, name: string): StudentTree {
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
      { week_number: 2, accuracy: 0.75, total_attempts: 10, correct_count: 8 },
    ],
    dominant_errors: ["E01"],
    total_attempts: 20,
    correct_count: 15,
    emotional_state: "stable",
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
    makeTree("S001", "小明"),
    makeTree("S002", "小红"),
    makeTree("S003", "小刚"),
  ],
  class_accuracy: 0.78,
  class_top_errors: ["E02", "E03"],
  class_emotional_state: "happy",
};

describe("ClassForestGrid", () => {
  it("renders correct number of student cards", () => {
    render(<ClassForestGrid forest={mockForest} />);
    expect(screen.getByText("小明")).toBeInTheDocument();
    expect(screen.getByText("小红")).toBeInTheDocument();
    expect(screen.getByText("小刚")).toBeInTheDocument();
  });

  it("displays class accuracy percentage", () => {
    render(<ClassForestGrid forest={mockForest} />);
    expect(screen.getByText("78%")).toBeInTheDocument();
  });

  it("shows class name", () => {
    render(<ClassForestGrid forest={mockForest} />);
    expect(screen.getByText("六年级一班")).toBeInTheDocument();
  });

  it("shows tree count", () => {
    render(<ClassForestGrid forest={mockForest} />);
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("棵小树")).toBeInTheDocument();
  });

  it("shows class emotional state", () => {
    render(<ClassForestGrid forest={mockForest} />);
    expect(screen.getByText(/开心成长/)).toBeInTheDocument();
  });
});
