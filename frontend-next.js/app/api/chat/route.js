import { createClient } from "@/utils/supabase/server";
import { NextResponse } from "next/server";

export async function POST(request) {
  try {
    // 1. Authenticate user
    const supabase = await createClient();
    const { data: { user }, error: authError } = await supabase.auth.getUser();

    if (authError || !user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    // 2. Validate request payload
    let body;
    try {
      body = await request.json();
    } catch {
      return NextResponse.json({ error: "Invalid request JSON" }, { status: 400 });
    }

    const { chatid, question } = body;
    if (!question || typeof question !== "string" || !question.trim()) {
      return NextResponse.json({ error: "question is required" }, { status: 400 });
    }

    let session = null;
    let actualChatId = chatid;

    // 3. Verify chat session ownership and active status if chatid is provided
    if (actualChatId) {
      const { data: existingSession, error: sessionError } = await supabase
        .from("chat_sessions")
        .select("chatid, title")
        .eq("chatid", actualChatId)
        .eq("user_id", user.id)
        .eq("status", "ACTIVE")
        .maybeSingle();

      if (sessionError) {
        console.error("Supabase chat session query error:", sessionError);
        return NextResponse.json({ error: "Supabase query failure" }, { status: 500 });
      }

      if (!existingSession) {
        return NextResponse.json({ error: "Unauthorized or chat session not found" }, { status: 404 });
      }
      session = existingSession;
    }

    // 4. Connect to FastAPI backend with timeout protection
    const fastapiUrl = process.env.FASTAPI_BASE_URL || "http://127.0.0.1:8000";
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30s timeout

    let fastapiRes;
    try {
      fastapiRes = await fetch(`${fastapiUrl}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: question.trim() }),
        signal: controller.signal
      });
      clearTimeout(timeoutId);
    } catch (fetchErr) {
      clearTimeout(timeoutId);
      console.error("FastAPI connection error:", fetchErr);
      if (fetchErr.name === "AbortError") {
        return NextResponse.json({ error: "Timeout waiting for backend response" }, { status: 504 });
      }
      return NextResponse.json({ error: "FastAPI unavailable" }, { status: 502 });
    }

    if (!fastapiRes.ok) {
      console.error(`FastAPI returned non-OK status: ${fastapiRes.status}`);
      return NextResponse.json({ error: "Failed response from core backend service" }, { status: fastapiRes.status });
    }

    // 5. Parse FastAPI response
    let result;
    try {
      result = await fastapiRes.json();
    } catch (parseErr) {
      console.error("Failed to parse FastAPI JSON response:", parseErr);
      return NextResponse.json({ error: "Invalid JSON response from backend" }, { status: 502 });
    }

    const { answer } = result;
    if (answer === undefined || answer === null) {
      console.error("FastAPI response missing 'answer' field:", result);
      return NextResponse.json({ error: "Invalid response format from backend" }, { status: 502 });
    }

    // 6. Create or update chat session dynamically
    if (!actualChatId) {
      const truncatedTitle = question.trim().length > 50 ? question.trim().slice(0, 47) + "..." : question.trim();
      const { data: newSession, error: newSessionError } = await supabase
        .from("chat_sessions")
        .insert({
          user_id: user.id,
          title: truncatedTitle,
          status: "ACTIVE"
        })
        .select("chatid")
        .single();

      if (newSessionError) {
        console.error("Error creating chat session dynamically:", newSessionError);
        return NextResponse.json({ error: "Failed to create chat session" }, { status: 500 });
      }
      actualChatId = newSession.chatid;
    } else {
      // Update session title if default, else bubble updated_at to top
      if (session.title === "New Chat") {
        const initialTitle = question.trim();
        const truncatedTitle = initialTitle.length > 50 ? initialTitle.slice(0, 47) + "..." : initialTitle;
        await supabase
          .from("chat_sessions")
          .update({ title: truncatedTitle, updated_at: new Date().toISOString() })
          .eq("chatid", actualChatId);
      } else {
        await supabase
          .from("chat_sessions")
          .update({ updated_at: new Date().toISOString() })
          .eq("chatid", actualChatId);
      }
    }

    // 7. Save user question & assistant answer to database in a single row
    const { data: newMsg, error: msgError } = await supabase
      .from("messages")
      .insert({
        chatid: actualChatId,
        user_id: user.id,
        question: question.trim(),
        answer: answer
      })
      .select("id, chatid, user_id, question, answer, created_at")
      .single();

    if (msgError) {
      console.error("Supabase QA message insert error:", msgError);
      return NextResponse.json({ error: "Supabase insert failure" }, { status: 500 });
    }

    // 8. Return answer, chatid and database message to client
    return NextResponse.json({ answer, chatid: actualChatId, message: newMsg });
  } catch (err) {
    console.error("Unexpected error in /api/chat Route Handler:", err);
    return NextResponse.json({ error: "Unexpected server exception" }, { status: 500 });
  }
}
