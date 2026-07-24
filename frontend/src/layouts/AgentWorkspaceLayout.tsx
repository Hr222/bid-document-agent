import { Bell, Bot, ChevronDown, FileText, GitBranch, Home, Library, MessageSquare, Settings, Sparkles } from "lucide-react";
import { Avatar, Badge, Breadcrumb, Input, Layout, Menu, type MenuProps } from "antd";
import { useMemo } from "react";
import { useLocation, useNavigate, Outlet } from "react-router-dom";

import styles from "./AgentWorkspaceLayout.module.css";

const { Header, Sider, Content } = Layout;

const menuItems: MenuProps["items"] = [
  { key: "/dashboard", icon: <Home size={17} />, label: "控制台" },
  { key: "/chat", icon: <MessageSquare size={17} />, label: "对话" },
  { key: "/agents", icon: <Bot size={17} />, label: "智能体" },
  { key: "/workflow", icon: <GitBranch size={17} />, label: "工作流" },
  { key: "/knowledge-bases", icon: <Library size={17} />, label: "知识库" },
];

const platformItems: MenuProps["items"] = [
  { key: "/docs", icon: <FileText size={17} />, label: "文档中心" },
  { key: "/settings", icon: <Settings size={17} />, label: "系统设置" },
];

export function AgentWorkspaceLayout() {
  const navigate = useNavigate();
  const location = useLocation();

  const selectedKey = useMemo(() => {
    if (location.pathname.startsWith("/knowledge-bases")) return "/knowledge-bases";
    return menuItems?.find((item) => item && "key" in item && location.pathname.startsWith(String(item.key)))?.key as string | undefined;
  }, [location.pathname]);

  const handleMenuClick: MenuProps["onClick"] = ({ key }) => {
    if (key === "/knowledge-bases") {
      navigate("/knowledge-bases");
      return;
    }
    navigate(key);
  };

  return (
    <Layout className={styles.layout}>
      <Sider width={252} className={styles.sider} theme="dark">
        <div className={styles.brand}>
          <div className={styles.brandMark}><Sparkles size={21} /></div>
          <div><div className={styles.brandName}>AetherFlow</div><div className={styles.brandCaption}>AI 智能工作台</div></div>
        </div>
        <div className={styles.sectionLabel}>工作区</div>
        <Menu className={styles.menu} theme="dark" mode="inline" selectedKeys={selectedKey ? [selectedKey] : []} items={menuItems} onClick={handleMenuClick} />
        <div className={styles.siderBottom}>
          <div className={styles.sectionLabel}>平台</div>
          <Menu className={styles.menu} theme="dark" mode="inline" selectedKeys={[]} items={platformItems} onClick={handleMenuClick} />
          <div className={styles.profile}>
            <Avatar className={styles.avatar}>陈</Avatar>
            <div className={styles.profileCopy}><strong>陈先生</strong><span>项目负责人</span></div>
            <ChevronDown size={14} color="#76839e" />
          </div>
        </div>
      </Sider>
      <Layout className={styles.contentLayout}>
        <Header className={styles.header}>
          <Breadcrumb className={styles.breadcrumb} items={[{ title: "工作区" }, { title: getBreadcrumbTitle(location.pathname) }]} />
          <div className={styles.headerActions}>
            <Input className={styles.globalSearch} prefix={<FileText size={14} color="#98a3b6" />} placeholder="搜索文档、智能体或任务..." />
            <Badge dot><Bell size={17} color="#78869c" /></Badge>
            <div className={styles.headerDivider} />
            <div className={styles.user}><Avatar className={styles.userAvatar}>陈</Avatar><span>陈先生</span><ChevronDown size={13} color="#9ba6b8" /></div>
          </div>
        </Header>
        <Content className={styles.main}><Outlet /></Content>
      </Layout>
    </Layout>
  );
}

function getBreadcrumbTitle(pathname: string) {
  if (pathname.startsWith("/chat")) return "对话";
  if (pathname.startsWith("/agents")) return pathname.includes("/tasks/") ? "Tender 任务" : "智能体";
  if (pathname.startsWith("/workflow")) return "工作流";
  if (pathname.startsWith("/knowledge-bases")) return "知识库";
  if (pathname.startsWith("/docs")) return "文档中心";
  if (pathname.startsWith("/settings")) return "系统设置";
  return "控制台";
}
