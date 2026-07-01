"use client";

import * as React from "react";
import { NavUser } from "@/components/sidebar/nav-user";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuAction,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { BotIcon, PlusIcon, Trash2Icon, MoreHorizontalIcon } from "lucide-react";
import { Spinner } from "@/components/ui/spinner";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

const user = {
  name: "shadcn",
  email: "m@example.com",
  avatar: "/avatars/shadcn.jpg",
};

export function AppSidebar({
  activeChatId,
  history = [],
  historyLoading,
  onSelectChat,
  onNewChat,
  onDeleteChat,
  onDeleteAllChats,
  ...props
}) {
  return (
    <Sidebar
      className="top-(--header-height) h-[calc(100svh-var(--header-height))]!"
      {...props}
    >
      {/* Brand header */}
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" asChild>
              <a href="#">
                <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
                  <BotIcon className="size-4" />
                </div>
                <div className="grid flex-1 text-left text-sm leading-tight">
                  <span className="truncate font-medium">Employee Handbook</span>
                  <span className="truncate text-xs">AI Assistant</span>
                </div>
              </a>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
 
        {/* New Chat Button */}
        <Button
          variant="ghost"
          className="w-full justify-start gap-2 rounded-md h-10 px-3 text-sm font-normal"
          onClick={onNewChat}
          aria-label="Start a new chat"
        >
          <PlusIcon className="size-4 shrink-0" />
          New Chat
        </Button>
 
        {/* Delete All History Button */}
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button
              variant="ghost"
              className="w-full justify-start gap-2 rounded-md h-10 px-3 text-sm font-normal text-muted-foreground hover:text-destructive hover:bg-destructive/10"
              aria-label="Delete all chat history"
            >
              <Trash2Icon className="size-4 shrink-0" />
              Delete All History
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete All Chats?</AlertDialogTitle>
              <AlertDialogDescription>
                This action cannot be undone. This will permanently delete all your chat history.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction onClick={onDeleteAllChats} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">Delete</AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </SidebarHeader>
 
      {/* Scrollable: History section */}
      <SidebarContent className="overflow-y-auto">
        <SidebarGroup>
          <SidebarGroupLabel>History</SidebarGroupLabel>
          <SidebarMenu>
            {historyLoading ? (
              <div className="flex items-center justify-center p-4">
                <Spinner className="h-4 w-4 text-muted-foreground" />
              </div>
            ) : history.length === 0 ? (
              <div className="text-xs text-muted-foreground p-4 text-center">No history yet</div>
            ) : (
              history.map((item) => (
                <SidebarMenuItem key={item.chatid}>
                  <SidebarMenuButton
                    asChild
                    isActive={item.chatid === activeChatId}
                    tooltip={item.title}
                  >
                    <a
                      href="#"
                      onClick={(e) => {
                        e.preventDefault();
                        onSelectChat(item.chatid);
                      }}
                    >
                      <span className="truncate">{item.title}</span>
                    </a>
                  </SidebarMenuButton>

                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <SidebarMenuAction showOnHover aria-label="Conversation options">
                        <MoreHorizontalIcon />
                        <span className="sr-only">More options</span>
                      </SidebarMenuAction>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent side="right" align="start" className="w-40">
                      <DropdownMenuItem
                        className="text-destructive focus:text-destructive focus:bg-destructive/10"
                        onClick={() => onDeleteChat(item.chatid)}
                      >
                        <Trash2Icon className="size-4 mr-2" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </SidebarMenuItem>
              ))
            )}
          </SidebarMenu>
        </SidebarGroup>
      </SidebarContent>
 
      {/* User nav footer */}
      <SidebarFooter>
        <NavUser user={user} />
      </SidebarFooter>
    </Sidebar>
  );
}