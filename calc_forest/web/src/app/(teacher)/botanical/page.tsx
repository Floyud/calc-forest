"use client";

import { useMemo, useState, useEffect, useRef } from "react";
import dynamic from "next/dynamic";
import { motion } from "framer-motion";
import { TreePine, Leaf, Calendar, Ruler, Sparkles, AlertCircle, ChevronDown, ChevronUp } from "lucide-react";
import { getTreeColors } from "@/components/forest/trees/treeColors";
import { useTreeSpecies } from "@/lib/api/hooks";
import { cn } from "@/lib/utils";
import type { TreeSpecies } from "@/lib/types";

const SvgTree = dynamic(
  () => import("@/components/forest/trees/SvgTree").then((m) => ({ default: m.SvgTree })),
  { ssr: false },
);

const EASE_OUT: [number, number, number, number] = [0.22, 1, 0.36, 1];

/* ─── Enrichment data for species not available from API ─── */

interface SpeciesEnrichment {
  latinName: string;
  description: string;
  facts: string[];
  season: string;
  growth: string;
  accentColor: string;
}

const SPECIES_ENRICHMENT: Record<string, SpeciesEnrichment> = {
  cherry: {
    latinName: "Prunus serrulata",
    description:
      "春天最美的花树之一，花朵像粉色云朵。日本国花，在中国也有悠久种植历史。",
    facts: [
      "樱花花期只有 7-14 天，非常珍贵",
      "花瓣可以用来做樱花饼，是春天的美味",
      "日本有\u201C花见\u201D赏樱传统，已有千年历史",
      "全世界有超过 600 种樱花",
    ],
    season: "3-4 月开花",
    growth: "高 4-16 米，寿命约 60-80 年",
    accentColor: "#FFB7D5",
  },
  apple: {
    latinName: "Malus domestica",
    description:
      "世界上最重要的果树之一，春天开白色小花，秋天结出红彤彤的苹果。",
    facts: [
      "苹果有 7500 多个品种，颜色味道各不同",
      "苹果种子里面含有微量氰化物，所以不要吃太多籽",
      "苹果能漂浮在水上，因为 25% 是空气",
      "世界上最大的苹果重达 1.8 公斤",
    ],
    season: "4 月开花，9-10 月结果",
    growth: "高 3-12 米，寿命约 50-100 年",
    accentColor: "#FF6B6B",
  },
  orange: {
    latinName: "Citrus reticulata",
    description:
      "中国传统果树，\u201C橘\u201D谐音\u201C吉\u201D，是春节必备的吉祥果。橘树四季常青。",
    facts: [
      "维生素 C 含量很高，吃橘子能预防感冒",
      "哥伦布把橘子带到了美洲，从此传播全世界",
      "一棵橘树可以活 100 年以上",
      "中国是橘子的原产地，种植历史超过 4000 年",
    ],
    season: "4-5 月开花，11-12 月结果",
    growth: "高 3-6 米，寿命约 50-100 年",
    accentColor: "#FFA940",
  },
  maple: {
    latinName: "Acer palmatum",
    description:
      "秋天最美的树！叶子会从绿色变成红色、橙色、黄色，像一幅天然油画。",
    facts: [
      "枫叶变红是因为叶绿素分解，花青素显现出来",
      "枫糖浆来自糖枫树的树液，需要煮很多才能做成",
      "加拿大国旗上就有一片红色的枫叶",
      "枫树的果实是带翅膀的\u201C直升机种子\u201D，会旋转飞落",
    ],
    season: "4-5 月开花，10-11 月叶色最艳",
    growth: "高 10-25 米，寿命约 100-300 年",
    accentColor: "#FFD700",
  },
  pine: {
    latinName: "Pinus",
    description:
      "四季常青的不老松！中国传统文化中象征长寿和坚韧。松树的叶子是针形的。",
    facts: [
      "有些松果需要火灾的高温才能打开，释放种子",
      "世界上最古老的树是一棵 4800 岁的刺果松",
      "松针可以用来泡茶，含有丰富的维生素",
      "松脂经过千万年可以变成琥珀，里面可能包裹着远古昆虫",
    ],
    season: "常绿树种，4-5 月长出新叶",
    growth: "高 3-50 米，寿命可达数千年",
    accentColor: "#66BB6A",
  },
  oak: {
    latinName: "Quercus",
    description:
      "森林之王！树冠宽大，是许多动物的家。橡果是松鼠最爱的食物。",
    facts: [
      "一棵成年橡树一年可以产出 7 万颗橡果",
      "橡木是做葡萄酒桶的最好材料，能让酒更香醇",
      "橡树可以活 1000 年以上，见证历史变迁",
      "橡树的根系可以延伸到地下 30 米，像巨大的锚",
    ],
    season: "5 月开花，9-10 月橡果成熟",
    growth: "高 15-30 米，寿命可达 1000 年",
    accentColor: "#A0785A",
  },
  wintersweet: {
    latinName: "Chimonanthus praecox",
    description: "冬天开花的坚韧植物，古诗词中常被赞美的凌寒之花。",
    facts: [
      "腊梅在寒冬腊月盛开，是冬天里少有的花",
      "腊梅的花朵像蜡做的，所以叫腊梅",
      "腊梅的香味清雅，可以提取香精",
      "腊梅象征着坚韧不拔的精神",
    ],
    season: "12-2 月开花",
    growth: "高 2-4 米，灌木",
    accentColor: "#FFD54F",
  },
  sunflower: {
    latinName: "Helianthus annuus",
    description: "永远追着太阳转的花！向日葵代表了积极向上的精神。",
    facts: [
      "向日葵的花盘会跟着太阳转，这叫向光性",
      "一颗向日葵可以结出 1000 多粒瓜子",
      "向日葵可以长到 3 米高",
      "向日葵的原产地是北美洲",
    ],
    season: "7-9 月开花",
    growth: "高 1-3 米，一年生草本",
    accentColor: "#FFC107",
  },
};

interface SpeciesCardData {
  id: string;
  name: string;
  emoji: string;
  educationValue: string;
  knowledgeHighlight: string;
  latinName: string;
  description: string;
  facts: string[];
  season: string;
  growth: string;
  accentColor: string;
}

function enrichSpecies(api: TreeSpecies): SpeciesCardData {
  const extra = SPECIES_ENRICHMENT[api.id] ?? {
    latinName: "",
    description: api.education_value,
    facts: [api.knowledge_highlight],
    season: "",
    growth: "",
    accentColor: "#6B7280",
  };
  return {
    id: api.id,
    name: api.name,
    emoji: api.emoji,
    educationValue: api.education_value,
    knowledgeHighlight: api.knowledge_highlight,
    ...extra,
  };
}

/* ─── Tree Preview ─── */

function SpeciesTreePreview({ speciesId }: { speciesId: string }) {
  const colors = useMemo(
    () => getTreeColors(speciesId, "happy"),
    [speciesId],
  );

  return (
    <div className="flex items-center justify-center py-4">
      <SvgTree
        stage="mature"
        emotion="happy"
        colors={colors}
        size={120}
        animate
      />
    </div>
  );
}

/* ─── Collapsible Facts ─── */

const VISIBLE_FACTS = 2;

function CollapsibleFacts({ facts, accentColor }: { facts: string[]; accentColor: string }) {
  const [expanded, setExpanded] = useState(false);
  const visibleFacts = expanded ? facts : facts.slice(0, VISIBLE_FACTS);
  const hasMore = facts.length > VISIBLE_FACTS;

  return (
    <div>
      <ul className="space-y-1.5">
        {visibleFacts.map((factText, i) => (
          <li key={i} className="flex items-start gap-2 text-[12px] leading-relaxed text-ink-300">
            <span
              className="mt-1.5 inline-block h-1.5 w-1.5 shrink-0 rounded-full"
              style={{ backgroundColor: accentColor }}
            />
            {factText}
          </li>
        ))}
      </ul>
      {hasMore && (
        <button
          onClick={() => setExpanded((v) => !v)}
          className="mt-2 flex items-center gap-1 text-[11px] font-medium transition-colors hover:text-ink-500"
          style={{ color: accentColor }}
        >
          {expanded ? (
            <><ChevronUp className="h-3 w-3" />收起</>
          ) : (
            <><ChevronDown className="h-3 w-3" />展开更多</>
          )}
        </button>
      )}
    </div>
  );
}

/* ─── Species Card ─── */

function SpeciesCard({
  species,
  index,
  featured = false,
}: {
  species: SpeciesCardData;
  index: number;
  featured?: boolean;
}) {
  return (
    <motion.article
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        delay: 0.08 + index * 0.07,
        duration: 0.45,
        ease: EASE_OUT,
      }}
      whileHover={{ y: -2 }}
      className={cn(
        "group relative overflow-hidden rounded-[22px] bg-parchment-50 transition-all duration-300 ease-[cubic-bezier(0.4,0,0.2,1)]",
        "hover:shadow-lg hover:shadow-forest-200/25",
        featured && "md:col-span-2 md:row-span-1",
      )}
    >
      {/* Accent top bar */}
      <div
        className="h-1 w-full"
        style={{ backgroundColor: species.accentColor }}
      />

      <div className="p-5 md:p-6">
        {/* Header: emoji + name */}
        <div className="mb-3 flex items-start gap-3">
          <span
            className={cn("leading-none", featured ? "text-4xl" : "text-3xl")}
            role="img"
            aria-label={species.name}
          >
            {species.emoji}
          </span>
          <div className="min-w-0 flex-1">
            <h3
              className={cn(
                "font-bold tracking-tight text-ink-500",
                featured ? "text-xl" : "text-lg",
              )}
            >
              {species.name}
            </h3>
            <p className="mt-0.5 text-[11px] italic text-ink-300">{species.latinName}</p>
          </div>
        </div>

        {/* Tree preview */}
        <div
          className={cn(
            "mb-3 rounded-xl bg-gradient-to-b from-forest-50/50 to-parchment-100/40",
            featured && "flex items-center justify-center",
          )}
        >
          <SpeciesTreePreview speciesId={species.id} />
        </div>

        {/* Description */}
        <p
          className={cn(
            "mb-4 text-[13px] leading-relaxed text-ink-400",
            featured && "max-w-lg",
          )}
        >
          {species.description}
        </p>

        {/* Fun facts */}
        <div className="mb-4">
          <div className="mb-2 flex items-center gap-1.5">
            <Sparkles className="h-3.5 w-3.5 text-warm-400" />
            <span className="text-[10px] font-semibold uppercase tracking-wider text-warm-500">
              趣味小知识
            </span>
          </div>
          <CollapsibleFacts facts={species.facts} accentColor={species.accentColor} />
        </div>

        {/* Meta info */}
        <div className="flex flex-col gap-1.5 border-t border-parchment-200/50 pt-3">
          <div className="flex items-center gap-2">
            <Calendar className="h-3 w-3 text-sage-400" />
            <span className="text-[11px] text-ink-300">
              <span className="font-medium text-ink-400">花果时节：</span>
              {species.season}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Ruler className="h-3 w-3 text-sage-400" />
            <span className="text-[11px] text-ink-300">
              <span className="font-medium text-ink-400">生长数据：</span>
              {species.growth}
            </span>
          </div>
        </div>
      </div>
    </motion.article>
  );
}

/* ─── Lazy-loaded Card Wrapper ─── */

const ABOVE_FOLD_COUNT = 3;

function LazySpeciesCard({ species, index, featured }: { species: SpeciesCardData; index: number; featured?: boolean }) {
  const [visible, setVisible] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { rootMargin: "200px" },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  if (!visible) {
    return (
      <div
        ref={ref}
        className={cn(
          "rounded-[22px] bg-parchment-50/30",
          featured ? "h-[440px] md:col-span-2" : "h-[440px]",
        )}
      />
    );
  }

  return (
    <div ref={ref}>
      <SpeciesCard species={species} index={index} featured={featured} />
    </div>
  );
}

/* ─── Main Page ─── */

export default function BotanicalPage() {
  const { data: apiSpecies, isLoading, isError } = useTreeSpecies();

  const species: SpeciesCardData[] = useMemo(() => {
    if (!apiSpecies) return [];
    return apiSpecies.map(enrichSpecies);
  }, [apiSpecies]);

  const featured = useMemo(() => species[0] ?? null, [species]);
  const rest = useMemo(() => (featured ? species.slice(1) : species), [species, featured]);
  const aboveFold = useMemo(() => rest.slice(0, ABOVE_FOLD_COUNT), [rest]);
  const belowFold = useMemo(() => rest.slice(ABOVE_FOLD_COUNT), [rest]);

  if (isLoading) {
    return (
      <div className="mx-auto max-w-6xl px-4 py-6 md:py-8">
        <div className="space-y-4">
          <div className="h-10 w-48 animate-pulse rounded-xl bg-muted" />
          <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
            <div className="h-[440px] animate-pulse rounded-[22px] bg-forest-100/50 md:col-span-2" />
            <div className="h-[440px] animate-pulse rounded-[22px] bg-forest-100/40" />
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-[440px] animate-pulse rounded-[22px] bg-forest-100/30" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="mx-auto max-w-6xl px-4 py-10">
        <div className="flex flex-col items-center justify-center gap-4 rounded-2xl border border-red-200 bg-red-50/40 p-10 text-center">
          <AlertCircle className="h-10 w-10 text-red-400" />
          <h2 className="text-base font-semibold text-red-700">无法加载树种数据</h2>
          <p className="text-[13px] text-red-600">
            请确认后端服务正在运行
          </p>
        </div>
      </div>
    );
  }

  if (species.length === 0) {
    return (
      <div className="mx-auto max-w-6xl px-4 py-10">
        <div className="flex flex-col items-center justify-center gap-4 rounded-2xl border border-forest-200 bg-forest-50/20 p-10 text-center">
          <TreePine className="h-10 w-10 text-forest-400" />
          <h2 className="text-base font-semibold text-forest-700">暂无树种数据</h2>
          <p className="text-[13px] text-forest-600">
            种子数据尚未加载，请联系管理员
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 md:py-8">
      {/* Hero */}
      <motion.header
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, ease: EASE_OUT }}
        className="mb-10 md:mb-14"
      >
        <div className="mb-5 flex items-center gap-3.5">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-forest-100 to-forest-200/60 shadow-sm">
            <TreePine className="h-6 w-6 text-forest-600" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-[var(--tone-ink)] md:text-3xl">
              小树百科
            </h1>
            <p className="mt-0.5 text-[12px] font-medium text-muted-foreground tracking-wide">
              树木植物园 · 认识森林里的每一种树
            </p>
          </div>
        </div>

        <p className="max-w-2xl pl-[58px] text-[13px] leading-[1.8] text-muted-foreground md:text-sm">
          欢迎来到小树百科！这里住着我们计算森林里的每一位树朋友。
          每种树都有自己独特的脾气和故事。有的春天开花最漂亮，有的秋天叶子会变色，
          还有的能活好几千年呢！一起来认识它们吧。
        </p>

        <div className="mt-6 flex items-center gap-2.5 pl-[58px]">
          <Leaf className="h-3.5 w-3.5 text-forest-400" />
          <div className="h-px flex-1 bg-gradient-to-r from-forest-200 via-parchment-300 to-transparent" />
          <span className="text-[11px] font-medium text-muted-foreground">
            {species.length} 种树种 · 用心呵护每一种成长
          </span>
        </div>
      </motion.header>

      {/* Featured card + sidebar layout (asymmetric) */}
      <section aria-label="树木百科卡片">
        {featured && (
          <div className="mb-5 grid grid-cols-1 gap-5 md:grid-cols-3">
            <div className="md:col-span-2">
              <SpeciesCard species={featured} index={0} featured />
            </div>
            {aboveFold[0] && (
              <SpeciesCard species={aboveFold[0]} index={1} />
            )}
          </div>
        )}

        {/* Rest of above-fold */}
        {featured && aboveFold.length > 1 && (
          <div className="mb-5 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {aboveFold.slice(1).map((s, i) => (
              <SpeciesCard key={s.id} species={s} index={i + 2} />
            ))}
          </div>
        )}

        {/* Below-fold (lazy) */}
        {belowFold.length > 0 && (
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {belowFold.map((s, i) => (
              <LazySpeciesCard key={s.id} species={s} index={ABOVE_FOLD_COUNT + 1 + i} />
            ))}
          </div>
        )}
      </section>

      {/* Footer */}
      <motion.footer
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6, duration: 0.5 }}
        className="mt-14 flex flex-col items-center gap-3 rounded-[22px] surface-soft px-6 py-10 text-center"
      >
        <div className="flex items-center gap-1.5 text-2xl">
          {"\u{1F331}"} {"\u{1F33F}"} {"\u{1F333}"} {"\u{1F338}"} {"\u{1F33A}"} {"\u{1F332}"}
        </div>
        <p className="max-w-md text-[14px] font-medium leading-relaxed text-[var(--tone-ink)]">
          每棵小树都有自己的故事，让我们一起成长吧！
        </p>
        <p className="text-[11px] text-muted-foreground">
          用心计算，用爱浇灌，小树苗终会长成参天大树。
        </p>
      </motion.footer>
    </div>
  );
}
