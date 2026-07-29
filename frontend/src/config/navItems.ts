import { Home, MessageSquare, FileText, Library, Key, BookOpen, Dumbbell, MessageCircleQuestion, TrendingUp } from "lucide-vue-next";

export interface NavItem {
  label: string;
  path: string;
  icon: typeof Home;
}

export interface NavGroup {
  label: string;
  icon: typeof Home;
  items: NavItem[];
}

/** 首页 — 始终置顶 */
export const homeItem: NavItem = { label: "首页", path: "/", icon: Home };

/** 论文工作台组 */
export const paperGroup: NavGroup = {
  label: "论文工作台",
  icon: FileText,
  items: [
    { label: "对话", path: "/chat", icon: MessageSquare },
    { label: "方案", path: "/solution", icon: FileText },
    { label: "知识库", path: "/knowledge", icon: Library },
  ],
};

/** 学习中心组 */
export const learnGroup: NavGroup = {
  label: "学习中心",
  icon: BookOpen,
  items: [
    { label: "学习工位", path: "/learn", icon: BookOpen },
    { label: "训练场", path: "/practice", icon: Dumbbell },
    { label: "答疑室", path: "/qa", icon: MessageCircleQuestion },
    { label: "成长档案", path: "/progress", icon: TrendingUp },
  ],
};

/** 底部固定项 */
export const bottomItems: NavItem[] = [
  { label: "API Keys", path: "/apikeys", icon: Key },
];

// ── 用于判断当前页面属于哪个组 ──

export const paperPaths = paperGroup.items.map((i) => i.path);
export const learnPaths = learnGroup.items.map((i) => i.path);
