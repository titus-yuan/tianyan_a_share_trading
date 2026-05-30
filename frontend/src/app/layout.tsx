import type { Metadata } from "next";
import TopNav from "@/components/layout/top-nav";
import Sidebar from "@/components/layout/sidebar";
import FooterBar from "@/components/layout/footer-bar";
import "./globals.css";

export const metadata: Metadata = {
  title: "天演 Tianyan",
  description: "A 股量化辅助系统 — 交易日历 · 推文监控 · 行情数据",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" className="h-full antialiased">
      <body className="h-full flex flex-col">
        <TopNav />
        <div className="flex flex-1 min-h-0">
          <Sidebar />
          <main className="flex-1 min-w-0 overflow-auto">{children}</main>
        </div>
        <FooterBar />
      </body>
    </html>
  );
}
