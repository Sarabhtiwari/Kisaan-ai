import { useState } from "react"
import { sendMessage } from "./api"
import Header from "./components/Header"
import MessageList from "./components/MessageList"
import ImagePreview from "./components/ImagePreview"
import InputBar from "./components/InputBar"

function App() {
  const [sessionId] = useState(
    "farmer_" + Math.random().toString(36).substr(2, 9)
  )
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

  // Handle image selection from InputBar
  function handleImageSelect(file) {
    setImage(URL.createObjectURL(file))
    const reader = new FileReader()
    reader.onload = () => {
      const base64 = reader.result.split(",")[1]
      setImageBase64(base64)
    }
    reader.readAsDataURL(file)
  }

  // Remove selected image
  function handleRemoveImage() {
    setImage(null)
    setImageBase64(null)
  }

  // Send message
  async function handleSend() {
    if (!input.trim() && !imageBase64) return
    if (loading) return

    const userMessage = input.trim()

    // Add user message
    setMessages(prev => [...prev, {
      role: "user",
      text: userMessage || "📷 Photo sent for analysis",
      image: image
    }])

    setInput("")
    setLoading(true)

    // Add empty AI bubble
    setMessages(prev => [...prev, {
      role: "ai",
      text: "",
      tool: ""
    }])

    try {
      await sendMessage(
        sessionId,
        userMessage,
        language,
        imageBase64,

        // onChunk
        (chunk) => {
          setMessages(prev => {
            const updated = [...prev]
            const last = updated[updated.length - 1]
            updated[updated.length - 1] = {
              ...last,
              text: last.text + chunk
            }
            return updated
          })
        },

        // onTool
        (tool) => {
          setMessages(prev => {
            const updated = [...prev]
            updated[updated.length - 1] = {
              ...updated[updated.length - 1],
              tool: tool
            }
            return updated
          })
        },

        // onDone
        () => {
          setLoading(false)
        }
      )

    } catch (error) {
      setMessages(prev => {
        const updated = [...prev]
        updated[updated.length - 1] = {
          ...updated[updated.length - 1],
          text: "माफ करें, कुछ गड़बड़ हो गई। कृपया दोबारा कोशिश करें।"
        }
        return updated
      })
      setLoading(false)
    }

    setImage(null)
    setImageBase64(null)
  }

  return (
    <div className="min-h-screen bg-green-50 flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-2xl bg-white rounded-2xl shadow-xl flex flex-col h-[90vh]">

        <Header
          language={language}
          onLanguageChange={setLanguage}
        />

        <MessageList
          messages={messages}
          loading={loading}
        />

        <ImagePreview
          image={image}
          onRemove={handleRemoveImage}
        />

        <InputBar
          input={input}
          onInputChange={setInput}
          onSend={handleSend}
          onImageSelect={handleImageSelect}
          loading={loading}
        />

      </div>
    </div>
  )
}

export default App