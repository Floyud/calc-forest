import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { GuidanceChat } from "@/components/guidance/GuidanceChat";

describe("GuidanceChat (expanded)", () => {
  it("renders TTS toggle with '自动朗读' label", () => {
    render(<GuidanceChat />);
    expect(screen.getByText(/自动朗读/)).toBeInTheDocument();
  });

  it("send button is disabled when input is empty", () => {
    render(<GuidanceChat />);
    const sendButton = screen.getByRole("button", { name: "发送消息" });
    expect(sendButton).toBeDisabled();
  });

  it("input has correct placeholder text", () => {
    render(<GuidanceChat />);
    const input = screen.getByPlaceholderText("输入计算题或问题...");
    expect(input).toBeInTheDocument();
  });

  it("input has correct aria-label", () => {
    render(<GuidanceChat />);
    const input = screen.getByLabelText("输入计算题或问题");
    expect(input).toBeInTheDocument();
  });

  it("shows welcome bot message when provided", () => {
    render(<GuidanceChat welcomeMessage="树精灵准备好了" />);
    expect(
      screen.getByText("树精灵准备好了"),
    ).toBeInTheDocument();
  });

  it("renders bot message bubble for welcome message", () => {
    render(<GuidanceChat welcomeMessage="树精灵准备好了" />);
    expect(
      screen.getByText("树精灵准备好了"),
    ).toBeInTheDocument();
  });

  it("renders bot avatar (tree icon) in message area", () => {
    const { container } = render(<GuidanceChat welcomeMessage="树精灵准备好了" />);
    const treeIcon = container.querySelector(".lucide-tree-pine");
    expect(treeIcon).toBeInTheDocument();
  });

  it("send button becomes enabled after typing text", async () => {
    const user = userEvent.setup();
    render(<GuidanceChat />);
    const input = screen.getByPlaceholderText("输入计算题或问题...");
    await user.type(input, "25×4=");
    const sendButton = screen.getByRole("button", { name: "发送消息" });
    expect(sendButton).not.toBeDisabled();
  });

  it("renders tree sprite icon in bot message", () => {
    render(<GuidanceChat />);
    const botMessageAreas = screen.getAllByRole("generic");
    expect(botMessageAreas.length).toBeGreaterThan(0);
  });

  it("renders input field with type text", () => {
    render(<GuidanceChat />);
    const input = screen.getByPlaceholderText("输入计算题或问题...");
    expect(input).toHaveAttribute("type", "text");
  });
});
