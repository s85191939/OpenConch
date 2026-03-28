import Anthropic from "@anthropic-ai/sdk";
import { NextRequest, NextResponse } from "next/server";

const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
});

/**
 * Extract memorable facts from a conversation using Claude.
 */
export async function POST(req: NextRequest) {
  const { conversation } = await req.json();

  try {
    const response = await anthropic.messages.create({
      model: "claude-sonnet-4-20250514",
      max_tokens: 512,
      messages: [
        {
          role: "user",
          content: `Extract key facts, preferences, and important information from this conversation that would be useful to remember for future interactions. Return ONLY a JSON array of short fact strings. If there's nothing worth remembering, return an empty array [].

Conversation:
${conversation}

JSON array of facts:`,
        },
      ],
    });

    const text = response.content[0].type === "text" ? response.content[0].text.trim() : "[]";

    // Parse JSON, handling markdown code blocks
    let cleaned = text;
    if (cleaned.startsWith("```")) {
      cleaned = cleaned.split("```")[1];
      if (cleaned.startsWith("json")) cleaned = cleaned.slice(4);
      cleaned = cleaned.trim();
    }

    const facts = JSON.parse(cleaned);
    return NextResponse.json({ facts: Array.isArray(facts) ? facts : [] });
  } catch {
    return NextResponse.json({ facts: [] });
  }
}
