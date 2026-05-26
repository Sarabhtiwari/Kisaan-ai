function MessageBubble({ message }) {
  const isUser = message.role === "user"

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      {/* Avatar for AI */}
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-green-600 flex items-center justify-center text-white text-xs mr-2 mt-1 flex-shrink-0">
          🌾
        </div>
      )}

      <div
        className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed ${
          isUser
            ? "bg-green-600 text-white rounded-br-sm"
            : "bg-gray-100 text-gray-800 rounded-bl-sm"
        }`}
      >
        {/* Crop image if sent */}
        {message.image && (
          <img
            src={message.image}
            alt="crop"
            className="rounded-lg mb-2 max-h-40 object-cover w-full"
          />
        )}

        {/* Message text */}
        <p className="whitespace-pre-wrap">{message.text}</p>

        {/* Tool badge */}
        {message.tool && (
          <div className="mt-2 flex items-center gap-1">
            <span className="text-xs opacity-50">🔧</span>
            <span className="text-xs opacity-50">{message.tool}</span>
          </div>
        )}
      </div>

      {/* Avatar for user */}
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-green-700 flex items-center justify-center text-white text-xs ml-2 mt-1 flex-shrink-0">
          👨‍🌾
        </div>
      )}
    </div>
  )
}

export default MessageBubble