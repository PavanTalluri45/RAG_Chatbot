import { createClient } from "@/utils/supabase/server";
import { NextResponse } from "next/server";

export async function POST(request) {
  try {
    const supabase = await createClient();
    const { data: { user }, error: authError } = await supabase.auth.getUser();

    if (authError || !user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    let body;
    try {
      body = await request.json();
    } catch {
      return NextResponse.json({ error: "Invalid request JSON" }, { status: 400 });
    }

    const { chatid } = body;
    if (!chatid) {
      return NextResponse.json({ error: "chatid is required" }, { status: 400 });
    }

    // Soft delete chat session: status = 'DELETED', deleted_at = now()
    const { data, error } = await supabase
      .from("chat_sessions")
      .update({
        status: "DELETED",
        deleted_at: new Date().toISOString()
      })
      .eq("chatid", chatid)
      .eq("user_id", user.id)
      .select("chatid")
      .maybeSingle();

    if (error) {
      console.error("Supabase soft delete update error:", error);
      return NextResponse.json({ error: "Supabase update failure" }, { status: 500 });
    }

    if (!data) {
      return NextResponse.json({ error: "Unauthorized or chat session not found" }, { status: 404 });
    }

    return NextResponse.json({ success: true });
  } catch (err) {
    console.error("Unexpected error in /api/delete-chat Route Handler:", err);
    return NextResponse.json({ error: "Unexpected server exception" }, { status: 500 });
  }
}
