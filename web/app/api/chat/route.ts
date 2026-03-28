import Anthropic from "@anthropic-ai/sdk";
import { NextRequest } from "next/server";

const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
});

export async function POST(req: NextRequest) {
  const { messages, memories } = await req.json();

  // Build system prompt with memory context
  let system = `You are a helpful AI assistant powered by OpenConch — you have persistent memory across conversations. You remember things the user has told you before and use that context naturally.

If you recall relevant memories, reference them naturally (e.g., "I remember you mentioned..."). If a memory seems outdated and the user corrects you, trust the user.

Be concise, helpful, and conversational.`;

  if (memories && memories.length > 0) {
    const memoryLines = memories.map((m: string) => `- ${m}`).join("\n");
    system += `\n\nThings I remember about this user from previous conversations:\n${memoryLines}`;
  }

  // Convert messages to Anthropic format
  const anthropicMessages = messages.map((m: { role: string; content: string }) => ({
    role: m.role as "user" | "assistant",
    content: m.content,
  }));

  // Stream the response
  const stream = anthropic.messages.stream({
    model: "claude-sonnet-4-20250514",
    max_tokens: 4096,
    system,
    messages: anthropicMessages,
  });

  // Create a readable stream for the response
  const encoder = new TextEncoder();
  const readable = new ReadableStream({
    async start(controller) {
      try {
        for await (const event of stream) {
          if (
            event.type === "content_block_delta" &&
            event.delta.type === "text_delta"
          ) {
            controller.enqueue(
              encoder.encode(`data: ${JSON.stringify({ text: event.delta.text })}\n\n`)
            );
          }
        }
        controller.enqueue(encoder.encode("data: [DONE]\n\n"));
        controller.close();
      } catch (error) {
        controller.enqueue(
          encoder.encode(
            `data: ${JSON.stringify({ error: "Stream error" })}\n\n`
          )
        );
        controller.close();
      }
    },
  });

  return new Response(readable, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}
