import "@testing-library/jest-dom/vitest";

// Mock framer-motion to avoid animation errors in tests
vi.mock("framer-motion", () => {
  const forwardRef =
    require("react").forwardRef ||
    ((render: any) => ({
      render,
      $$typeof: Symbol.for("react.forward_ref"),
    }));

  const Actual = require("framer-motion");

  return {
    ...Actual,
    AnimatePresence: ({ children }: any) => children,
    motion: new Proxy(
      {},
      {
        get: (_, tag) =>
          forwardRef(
            (
              { initial, animate, exit, transition, whileHover, whileTap, variants, style, ...rest }: any,
              ref: any,
            ) =>
              require("react").createElement(tag as string, { ...rest, style, ref }),
          ),
      },
    ),
  };
});

// Mock next/dynamic
vi.mock("next/dynamic", () => ({
  __esModule: true,
  default: (loader: any) => {
    // Return a component that renders the loaded component synchronously
    // For tests, we just return a placeholder
    const Component = (props: any) => {
      return require("react").createElement("div", { "data-testid": "dynamic-component" });
    };
    Component.displayName = "DynamicComponent";
    return Component;
  },
}));

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
  }),
  usePathname: () => "/",
  useSearchParams: () => new URLSearchParams(),
}));

// Mock next/link
vi.mock("next/link", () => ({
  __esModule: true,
  default: ({ children, ...props }: any) =>
    require("react").createElement("a", props, children),
}));
