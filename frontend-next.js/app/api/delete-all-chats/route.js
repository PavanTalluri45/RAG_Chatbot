import { createClient } from "@/utils/supabase/server";
import { NextResponse } from "next/server";

export async function POST(request) {
  try {
    const supabase = await createClient();
    const { data: { user }, error: authError } = await supabase.auth.getUser();

    if (authError || !user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    // Soft delete all ACTIVE chat sessions for the authenticated user
    const { error } = await supabase
      .from("chat_sessions")
      .update({
        status: "DELETED",
        deleted_at: new Date().toISOString()
      })
      .eq("user_id", user.id)
      .eq("status", "ACTIVE");

    if (error) {
      console.error("Supabase soft delete all update error:", error);
      return NextResponse.json({ error: "Supabase update failure" }, { status: 500 });
    }

    return NextResponse.json({ success: true });
  } catch (err) {
    console.error("Unexpected error in /api/delete-all-chats Route Handler:", err);
    return NextResponse.json({ error: "Unexpected server exception" }, { status: 500 });
  }
}
