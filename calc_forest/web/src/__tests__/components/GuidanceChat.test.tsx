import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { GuidanceChat } from "@/components/guidance/GuidanceChat";

describe("GuidanceChat", () => {
  it("renders input field", () => {
    render(<GuidanceChat />);
    expect(
      screen.getByPlaceholderText("输入计算题或问题..."),
    ).toBeInTheDocument();
  });

  it("renders send button", () => {
    render(<GuidanceChat />);
    expect(
      screen.getByRole("button", { name: "发送消息" }),
    ).toBeInTheDocument();
  });

  it("shows config message when no DIFY_API_KEY is set", () => {
    render(<GuidanceChat />);
    expect(
      screen.getByText("树精灵服务尚未配置，请联系老师"),
    ).toBeInTheDocument();
  });

  it("shows a bot message on mount when welcome message is provided", () => {
    const { container } = render(<GuidanceChat welcomeMessage="你好，我是树精灵！" />);
    const botMessages = container.querySelectorAll(".bg-forest-100 span");
    expect(botMessages.length).toBeGreaterThanOrEqual(1);
  });

  it("renders auto-read toggle header", () => {
    render(<GuidanceChat />);
    expect(screen.getByText(/自动朗读/)).toBeInTheDocument();
  });
});
