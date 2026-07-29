import { Home, MessageSquare, GraduationCap, FileText, Library, Key, BookOpen, Dumbbell, MessageCircleQuestion, TrendingUp } from "lucide-vue-next";

export interface NavItem {
  label: string;
  path: string;
  icon: typeof Home;
}

export const navItems: NavItem[] = [
  { label: "首页", path: "/", icon: Home },
  { label: "对话", path: "/chat", icon: MessageSquare },
  { label: "教学", path: "/teach", icon: GraduationCap },
  { label: "方案", path: "/solution", icon: FileText },
  { label: "学习工位", path: "/learn", icon: BookOpen },
  { label: "训练场", path: "/practice", icon: Dumbbell },
  { label: "答疑室", path: "/qa", icon: MessageCircleQuestion },
  { label: "成长档案", path: "/progress", icon: TrendingUp },
  { label: "知识库", path: "/knowledge", icon: Library },
  { label: "API Keys", path: "/apikeys", icon: Key },
];
