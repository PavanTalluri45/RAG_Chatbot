"use client";

import { AppSidebar } from "@/components/sidebar/app-sidebar";
import { SiteHeader } from "@/components/header/site-header";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { ChatLayout } from "@/components/chat/chat-layout";
import { useAuth } from "@/context/AuthContext";
import { useEffect, useState, useCallback } from "react";
import { toast } from "sonner";

export default function Home() {
  const { user, loading } = useAuth();
  const [open, setOpen] = useState(false);
  const [activeChatId, setActiveChatId] = useState(null);
  const [history, setHistory] = useState([]);
  const [messages, setMessages] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [messagesLoading, setMessagesLoading] = useState(false);

  // Fetch active chat sessions list (only status = 'ACTIVE')
  const fetchHistory = useCallback(async () => {
    setHistoryLoading(true);
    try {
      const res = await fetch("/api/chat-history");
      if (!res.ok) {
        throw new Error("Failed to load chat history");
      }
      const data = await res.json();
      setHistory(data.sessions || []);
    } catch (err) {
      console.error("Error loading chat history:", err);
      toast.error("Could not load chat history");
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  // Fetch messages for a specific active chat session
  const fetchMessages = useCallback(async (chatId) => {
    setMessagesLoading(true);
    try {
      const res = await fetch(`/api/chat-history?chatid=${chatId}`);
      if (!res.ok) {
        throw new Error("Failed to load messages");
      }
      const data = await res.json();
      setMessages(data.messages || []);
    } catch (err) {
      console.error("Error loading messages:", err);
      toast.error("Could not load chat messages");
    } finally {
      setMessagesLoading(false);
    }
  }, []);

  // Initialize history on mount and auth state change
  useEffect(() => {
    if (!loading && user) {
      fetchHistory();
      setOpen(true);
    } else if (!loading && !user) {
      setOpen(false);
      setHistory([]);
      setMessages([]);
      setActiveChatId(null);
    }
  }, [user, loading, fetchHistory]);

  // Handle New Chat creation
  const handleNewChat = useCallback(() => {
    setActiveChatId(null);
    setMessages([]);
    toast.success("Started a new conversation");
  }, []);

  // Handle Chat selection
  const handleSelectChat = useCallback((chatId) => {
    setActiveChatId(chatId);
    fetchMessages(chatId);
  }, [fetchMessages]);

  // Handle Chat deletion (soft delete)
  const handleDeleteChat = useCallback(async (chatId) => {
    try {
      const res = await fetch("/api/delete-chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chatid: chatId }),
      });
      if (!res.ok) {
        throw new Error("Failed to delete chat");
      }
      await fetchHistory();
      if (activeChatId === chatId) {
        setActiveChatId(null);
        setMessages([]);
      }
      toast.success("Conversation deleted");
    } catch (err) {
      console.error("Error deleting chat:", err);
      toast.error("Could not delete conversation");
    }
  }, [activeChatId, fetchHistory]);

  // Handle Delete All History (soft delete all)
  const handleDeleteAllChats = useCallback(async () => {
    try {
      const res = await fetch("/api/delete-all-chats", {
        method: "POST",
      });
      if (!res.ok) {
        throw new Error("Failed to delete all conversations");
      }
      await fetchHistory();
      setActiveChatId(null);
      setMessages([]);
      toast.success("All conversations cleared");
    } catch (err) {
      console.error("Error deleting all chats:", err);
      toast.error("Could not clear conversation history");
    }
  }, [fetchHistory]);

  return (
    <div className="[--header-height:calc(--spacing(14))]">
      <SidebarProvider
        className="flex flex-col"
        open={open}
        onOpenChange={setOpen}
      >
        <SiteHeader />
        <div className="flex flex-1 min-h-0 overflow-hidden">
          {!loading && user && (
            <AppSidebar
              activeChatId={activeChatId}
              history={history}
              historyLoading={historyLoading}
              onSelectChat={handleSelectChat}
              onNewChat={handleNewChat}
              onDeleteChat={handleDeleteChat}
              onDeleteAllChats={handleDeleteAllChats}
            />
          )}
          <SidebarInset className="flex flex-col min-h-0 overflow-hidden">
            <ChatLayout
              activeChatId={activeChatId}
              setActiveChatId={setActiveChatId}
              messages={messages}
              setMessages={setMessages}
              refreshHistory={fetchHistory}
              messagesLoading={messagesLoading}
            />
          </SidebarInset>
        </div>
      </SidebarProvider>
    </div>
  );
}
