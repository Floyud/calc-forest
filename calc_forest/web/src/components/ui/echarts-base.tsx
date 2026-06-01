"use client";

import { useEffect, useRef, useCallback, useMemo } from "react";
import type { EChartsOption } from "echarts";
import type { EChartsType } from "echarts/core";

/**
 * Lightweight ECharts wrapper for Next.js "use client" components.
 *
 * - Handles init / resize / dispose lifecycle
 * - Dynamic-imports echarts to avoid SSR issues
 * - Responsive via ResizeObserver
 * - Chinese locale (zh_CN) applied globally on first import
 */
interface EChartsBaseProps {
  /** Full ECharts option object */
  option: EChartsOption;
  /** Optional click handler — receives params from ECharts click event */
  onClick?: (params: Record<string, unknown>) => void;
  /** Additional CSS class on the container div */
  className?: string;
  /** Inline style overrides (width/height should be set via className) */
  style?: React.CSSProperties;
  /** Chart theme name (optional) */
  theme?: string;
}

export function EChartsBase({
  option,
  onClick,
  className = "h-full w-full",
  style,
  theme,
}: EChartsBaseProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<EChartsType | null>(null);
  const initPromiseRef = useRef<Promise<EChartsType | null> | null>(null);

  // Lazy-init the chart instance (dynamic import to avoid SSR)
  const getChart = useCallback(async (): Promise<EChartsType | null> => {
    if (chartRef.current) return chartRef.current;
    if (!containerRef.current) return null;

    // Reuse in-flight init if present
    if (initPromiseRef.current) return initPromiseRef.current;

    initPromiseRef.current = (async () => {
      const echarts = await import("echarts/core");
      const {
        RadarChart,
        LineChart,
        BarChart,
        HeatmapChart,
        GaugeChart,
      } = await import("echarts/charts");
      const {
        TitleComponent,
        TooltipComponent,
        GridComponent,
        PolarComponent,
        RadarComponent,
        VisualMapComponent,
      } = await import("echarts/components");
      const { CanvasRenderer } = await import("echarts/renderers");

      if (!containerRef.current) return null;

      echarts.use([
        RadarChart,
        LineChart,
        BarChart,
        HeatmapChart,
        GaugeChart,
        TitleComponent,
        TooltipComponent,
        GridComponent,
        PolarComponent,
        RadarComponent,
        VisualMapComponent,
        CanvasRenderer,
      ]);

      if (!containerRef.current) return null;
      const instance = echarts.init(containerRef.current, theme, {
        locale: "ZH",
        renderer: "canvas",
        // 启用 GPU 加速渲染
        useDirtyRect: true,
      });
      chartRef.current = instance;
      initPromiseRef.current = null;
      return instance;
    })();

    return initPromiseRef.current;
  }, [theme]);

  // Sync option to chart
  useEffect(() => {
    let cancelled = false;
    getChart().then((chart) => {
      if (!cancelled && chart) {
        chart.setOption(option, { notMerge: false });
        // 丝滑动效：缓入缓出，800ms 过渡
        chart.setOption({
          animation: true,
          animationDuration: 800,
          animationDurationUpdate: 600,
          animationEasing: "cubicInOut",
          animationEasingUpdate: "cubicInOut",
        } as EChartsOption, { notMerge: false });
      }
    });
    return () => {
      cancelled = true;
    };
  }, [option, getChart]);

  // Click handler
  useEffect(() => {
    if (!onClick) return;
    let cancelled = false;
    getChart().then((chart) => {
      if (!cancelled && chart) {
        chart.on("click", (params: Record<string, unknown>) => {
          onClick(params);
        });
      }
    });
    return () => {
      cancelled = true;
    };
  }, [onClick, getChart]);

  // Resize observer
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => {
      chartRef.current?.resize();
    });
    ro.observe(el);
    return () => {
      ro.disconnect();
    };
  }, []);

  // Dispose on unmount
  useEffect(() => {
    return () => {
      chartRef.current?.dispose();
      chartRef.current = null;
    };
  }, []);

  return <div ref={containerRef} className={className} style={{ ...style, willChange: "contents" }} />;
}
