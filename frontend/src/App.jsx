import { useState, useRef, useEffect } from "react"
import { sendMessage } from "./api"

function App() {
  const [messages, setMessages] = useState([
    {
      role: "ai",
      text: "नमस्ते किसान जी! मैं किसान AI हूँ। आप मुझसे फसल, मौसम, मंडी भाव या सरकारी योजनाओं के बारे में पूछ सकते हैं।"
    }
  ])
  const [input, setInput] = useState("")
  const [language, setLanguage] = useState("hi")
  const [loading, setLoading] = useState(false)
  const [image, setImage] = useState(null)
  const [imageBase64, setImageBase64] = useState(null)
  const bottomRef = useRef(null)
  const fileRef = useRef(null)

  // Auto scroll to bottom on new message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  // Convert image to base64 when farmer selects one
  function handleImageSelect(e) {
    const file = e.target.files[0]
    if (!file) return

    setImage(URL.createObjectURL(file))

    const reader = new FileReader()
    reader.onload = () => {
      // Remove the "data:image/jpeg;base64," prefix
      const base64 = reader.result.split(",")[1]
      setImageBase64(base64)
    }
    reader.readAsDataURL(file)
  }

  // Remove selected image
  function removeImage() {
    setImage(null)
    setImageBase64(null)
    fileRef.current.value = ""
  }

  // Send message to backend
  async function handleSend() {
    if (!input.trim() && !imageBase64) return
    if (loading) return

    const userMessage = input.trim()

    // Add farmer message to chat
    setMessages(prev => [...prev, {
      role: "user",
      text: userMessage || "📷 Photo sent for analysis",
      image: image
    }])

    setInput("")
    setLoading(true)

    try {
      const data = await sendMessage(userMessage, language, imageBase64)

      // Add AI response to chat
      setMessages(prev => [...prev, {
        role: "ai",
        text: data.reply,
        tool: data.tool_used
      }])

    } catch (error) {
      setMessages(prev => [...prev, {
        role: "ai",
        text: "माफ करें, कुछ गड़बड़ हो गई। कृपया दोबारा कोशिश करें।"
      }])
    }

    setLoading(false)
    setImage(null)
    setImageBase64(null)
    if (fileRef.current) fileRef.current.value = ""
  }

  // Send on Enter key
  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="min-h-screen bg-green-50 flex flex-col items-center justify-center p-4">

      {/* Chat Container */}
      <div className="w-full max-w-2xl bg-white rounded-2xl shadow-xl flex flex-col h-[90vh]">

        {/* Header */}
        <div className="bg-green-600 text-white px-6 py-4 rounded-t-2xl flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold">🌾 किसान AI</h1>
            <p className="text-green-100 text-sm">आपका कृषि सहायक</p>
          </div>

          {/* Language Selector */}
          <select
            value={language}
            onChange={e => setLanguage(e.target.value)}
            className="bg-green-700 text-white text-sm rounded-lg px-3 py-1 border border-green-500"
          >
            <option value="hi">हिंदी</option>
            <option value="en">English</option>
            <option value="pa">ਪੰਜਾਬੀ</option>
            <option value="mr">मराठी</option>
            <option value="te">తెలుగు</option>
          </select>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                  msg.role === "user"
                    ? "bg-green-600 text-white rounded-br-sm"
                    : "bg-gray-100 text-gray-800 rounded-bl-sm"
                }`}
              >
                {/* Show image if sent */}
                {msg.image && (
                  <img
                    src={msg.image}
                    alt="crop"
                    className="rounded-lg mb-2 max-h-40 object-cover"
                  />
                )}
                <p>{msg.text}</p>

                {/* Show which tool was used */}
                {msg.tool && (
                  <p className="text-xs mt-1 opacity-60">
                    🔧 {msg.tool}
                  </p>
                )}
              </div>
            </div>
          ))}

          {/* Loading indicator */}
          {loading && (
            <div className="flex justify-start">
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

        {/* Image Preview */}
        {image && (
          <div className="px-4 pb-2 flex items-center gap-2">
            <img
              src={image}
              alt="preview"
              className="h-16 w-16 object-cover rounded-lg border border-green-300"
            />
            <button
              onClick={removeImage}
              className="text-red-500 text-sm font-medium"
            >
              ✕ Remove
            </button>
          </div>
        )}

        {/* Input Bar */}
        <div className="px-4 py-3 border-t border-gray-200 flex items-center gap-2">

          {/* Image Upload Button */}
          <button
            onClick={() => fileRef.current.click()}
            className="text-green-600 hover:text-green-800 text-xl p-2"
            title="Upload crop photo"
          >
            📷
          </button>
          <input
            type="file"
            accept="image/*"
            ref={fileRef}
            onChange={handleImageSelect}
            className="hidden"
          />

          {/* Text Input */}
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="अपना सवाल यहाँ लिखें..."
            className="flex-1 border border-gray-300 rounded-full px-4 py-2 text-sm focus:outline-none focus:border-green-500"
          />

          {/* Send Button */}
          <button
            onClick={handleSend}
            disabled={loading}
            className="bg-green-600 hover:bg-green-700 text-white rounded-full px-4 py-2 text-sm font-medium disabled:opacity-50"
          >
            भेजें
          </button>
        </div>

      </div>
    </div>
  )
}

export default App