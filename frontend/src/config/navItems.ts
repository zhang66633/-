import {
  BookOpen,
  Dumbbell,
  FileText,
  Home,
  Key,
  Library,
  MessageSquare,
  TrendingUp,
} from "lucide-vue-next";

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

// 朋友用: 平面列表
export const navItems: NavItem[] = [
  { label: "首页", path: "/", icon: Home },
  { label: "对话", path: "/chat", icon: MessageSquare },
  { label: "方案", path: "/solution", icon: FileText },
  { label: "学习工位", path: "/learn", icon: BookOpen },
  { label: "训练场", path: "/practice", icon: Dumbbell },
  { label: "成长档案", path: "/progress", icon: TrendingUp },
  { label: "知识库", path: "/knowledge", icon: Library },
  { label: "API Keys", path: "/apikeys", icon: Key },
];

// AppSidebar 用: 分组结构
export const paperGroup: NavGroup = {
  label: "论文工作台",
  icon: FileText,
  items: [
    { label: "对话", path: "/chat", icon: MessageSquare },
    { label: "方案", path: "/solution", icon: FileText },
    { label: "知识库", path: "/knowledge", icon: Library },
  ],
};

export const learnGroup: NavGroup = {
  label: "学习中心",
  icon: BookOpen,
  items: [
    { label: "学习工位", path: "/learn", icon: BookOpen },
    { label: "训练场", path: "/practice", icon: Dumbbell },
    { label: "成长档案", path: "/progress", icon: TrendingUp },
  ],
};

export const bottomItems: NavItem[] = [
  { label: "API Keys", path: "/apikeys", icon: Key },
];
export const paperPaths = paperGroup.items.map((i) => i.path);
export const learnPaths = learnGroup.items.map((i) => i.path);
