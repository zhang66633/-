/** 项目统一的 Tailwind 样式常量。
 *
 * 所有按钮、交互元素从此引入，禁止在各页面模板中硬编码重复类名。
 */

// ── 缩放动画 ──
/* 两段式：悬停 → 2%，按下 → 3%（完整版，含 transition） */
export const SCALE_PRESS =
  "transition-transform hover:scale-[0.98] active:scale-[0.97]";
/* 仅缩放部分，用于已有 transition 的组件（如 shadcn Button） */
export const SCALE_PRESS_ONLY = "hover:scale-[0.98] active:scale-[0.97]";

// ── 按钮 ──
export const BTN_PRIMARY = [
  "group inline-flex items-center gap-2 rounded-md",
  "bg-foreground px-5 py-2.5 text-sm font-medium text-background",
  SCALE_PRESS,
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
].join(" ");

// ── 导航 ──
export const NAV_ITEM = [
  "group relative flex w-full items-center gap-3 py-2 pr-4 pl-2.5 text-sm",
  SCALE_PRESS,
].join(" ");
