import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { Navbar } from "@/components/layout/navbar";

vi.mock("@/components/auth/AuthProvider", () => ({
  useAuth: () => ({
    teacher: null,
    loading: false,
    login: vi.fn(),
    logout: vi.fn(),
  }),
}));

const NAV_ITEMS = [
  { label: "工作台", href: "/" },
  { label: "课堂模式", href: "/classroom" },
  { label: "诊断台", href: "/diagnose" },
  { label: "作业批阅", href: "/homework" },
];

describe("Navbar", () => {
  it("renders brand text '我的计算森林'", () => {
    render(<Navbar />);
    expect(screen.getByText("我的计算森林")).toBeInTheDocument();
  });

  it("renders all main navigation links", () => {
    render(<Navbar />);
    for (const item of NAV_ITEMS) {
      expect(screen.getByText(item.label)).toBeInTheDocument();
    }
  });

  it("renders links with correct href values", () => {
    render(<Navbar />);
    for (const item of NAV_ITEMS) {
      const link = screen.getByText(item.label).closest("a");
      expect(link).toHaveAttribute("href", item.href);
    }
  });

  it("renders secondary navigation dropdown button", () => {
    render(<Navbar />);
    expect(screen.getByText("品牌与演示")).toBeInTheDocument();
  });

  it("renders mobile menu toggle button", () => {
    render(<Navbar />);
    expect(screen.getByLabelText("切换菜单")).toBeInTheDocument();
  });

  it("renders header element", () => {
    const { container } = render(<Navbar />);
    const header = container.querySelector("header");
    expect(header).toBeInTheDocument();
  });
});
