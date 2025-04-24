"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, MessageSquare, Settings, ArrowRightLeft, Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTheme } from "next-themes";

export default function Sidebar() {
  const pathname = usePathname();
  const { theme, setTheme } = useTheme();
  const [expanded, setExpanded] = useState(true);

  const navItems = [
    { href: "/", label: "Dashboard", icon: LayoutDashboard },
    { href: "/chat", label: "Chat", icon: MessageSquare },
    { href: "/settings", label: "Configurações", icon: Settings },
  ];

  const toggleTheme = () => {
    setTheme(theme === "dark" ? "light" : "dark");
  };

  const toggleSidebar = () => {
    setExpanded(!expanded);
  };

  return (
    <div
      className={`h-screen bg-card text-card-foreground border-r flex flex-col transition-all duration-300 ${
        expanded ? "w-64" : "w-16"
      }`}
    >
      <div className="p-4 flex items-center justify-between border-b">
        {expanded && (
          <h1 className="font-bold text-lg">
            <span className="text-primary">Zabbia</span>
          </h1>
        )}
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleSidebar}
          aria-label={expanded ? "Recolher menu" : "Expandir menu"}
        >
          <ArrowRightLeft className="h-4 w-4" />
        </Button>
      </div>

      <nav className="flex-1 p-2">
        <ul className="space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            
            return (
              <li key={item.href}>
                <Link href={item.href}>
                  <Button
                    variant={isActive ? "secondary" : "ghost"}
                    className={`w-full justify-${expanded ? "start" : "center"}`}
                  >
                    <Icon className={`h-5 w-5 ${expanded ? "mr-2" : ""}`} />
                    {expanded && <span>{item.label}</span>}
                  </Button>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
      
      <div className="p-4 border-t flex justify-center">
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleTheme}
          aria-label="Alternar tema"
          title="Alternar tema"
        >
          {theme === "dark" ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
        </Button>
      </div>
    </div>
  );
} 