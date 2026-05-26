import { useEffect, useRef } from "react"
import MessageBubble from "./MessageBubble"

function MessageList({ messages, loading }) {
  const bottomRef = useRef(null)

  // Auto scroll to bottom on new message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  return (
    <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">

      {messages.map((msg, index) => (
        <MessageBubble key={index} message={msg} />
      ))}

      {/* Typing indicator */}
      {loading && (
        <div className="flex justify-start items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-green-600 flex items-center justify-center text-white text-xs flex-shrink-0">
            🌾
          </div>
          <div className="bg-gray-100 px-4 py-3 rounded-2xl rounded-bl-sm">
            <div className="flex space-x-1">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce delay-100"></div>
              <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce delay-200"></div>
            </div>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  )
}

export default MessageList