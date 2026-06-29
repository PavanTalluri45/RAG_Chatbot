import { createClient } from "@/utils/supabase/server";
import { NextResponse } from "next/server";

export async function GET(request) {
  try {
    const supabase = await createClient();
    const { data: { user }, error: authError } = await supabase.auth.getUser();

    if (authError || !user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const chatid = searchParams.get("chatid");

    if (chatid) {
      // 1. Verify user owns the requested chat session
      const { data: session, error: sessionError } = await supabase
        .from("chat_sessions")
        .select("chatid")
        .eq("chatid", chatid)
        .eq("user_id", user.id)
        .eq("status", "ACTIVE")
        .maybeSingle();

      if (sessionError) {
        console.error("Error querying chat session ownership:", sessionError);
        return NextResponse.json({ error: "Supabase query failure" }, { status: 500 });
      }

      if (!session) {
        return NextResponse.json({ error: "Unauthorized or chat session not found" }, { status: 404 });
      }

      // 2. Fetch all messages in this chat session
      const { data: dbMessages, error: messagesError } = await supabase
        .from("messages")
        .select("id, chatid, user_id, question, answer, created_at")
        .eq("chatid", chatid)
        .order("created_at", { ascending: true });

      if (messagesError) {
        console.error("Error querying messages:", messagesError);
        return NextResponse.json({ error: "Supabase query failure" }, { status: 500 });
      }

      return NextResponse.json({ messages: dbMessages });
    } else {
      // Fetch all active chat sessions for this user
      const { data: sessions, error: sessionsError } = await supabase
        .from("chat_sessions")
        .select("chatid, title, updated_at, created_at")
        .eq("user_id", user.id)
        .eq("status", "ACTIVE")
        .order("updated_at", { ascending: false });

      if (sessionsError) {
        console.error("Error querying chat sessions:", sessionsError);
        return NextResponse.json({ error: "Supabase query failure" }, { status: 500 });
      }

      return NextResponse.json({ sessions });
    }
  } catch (err) {
    console.error("Unexpected error in /api/chat-history Route Handler:", err);
    return NextResponse.json({ error: "Unexpected server exception" }, { status: 500 });
  }
}
