// In production API is on same domain (/api)
// In development it is on localhost:8000
const BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api"

export async function sendMessage(
  sessionId,
  message,
  language,
  imageBase64,
  onChunk,   // called for every word that arrives
  onTool,    // called when we know which tool was used
  onDone     // called when streaming is complete
) {
  const response = await fetch(`${BASE_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      session_id:   sessionId,
      message:      message,
      language:     language || "hi",
      image_base64: imageBase64 || null,
      location:     { city: "Lucknow" }
    })
  })

  // Get a reader to read chunks as they arrive
  const reader = response.body.getReader()
  const decoder = new TextDecoder()

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    // Decode the chunk bytes to text
    const text = decoder.decode(value)

    // Each chunk may contain multiple lines
    const lines = text.split("\n")

    for (const line of lines) {
      // SSE lines start with "data: "
      if (line.startsWith("data: ")) {
        try {
          const data = JSON.parse(line.slice(6))

          if (data.type === "tool")  onTool(data.tool)
          if (data.type === "chunk") onChunk(data.content)
          if (data.type === "done")  onDone()

        } catch (e) {
          // Incomplete chunk — skip it
        }
      }
    }
  }
}