import { createBrowserClient } from "@supabase/ssr";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;

export const createClient = () => {
    return createBrowserClient(supabaseUrl, supabaseKey, {
        cookieOptions: {
            maxAge: 60 * 60 * 24 * 2, // 2 days in seconds
            sameSite: "lax",
            secure: process.env.NODE_ENV === "production",
        },
    });
};