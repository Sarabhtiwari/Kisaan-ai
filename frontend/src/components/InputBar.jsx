import { useRef } from "react"

function InputBar({ input, onInputChange, onSend, onImageSelect, loading }) {
  const fileRef = useRef(null)

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      onSend()
    }
  }

  function handleFileChange(e) {
    const file = e.target.files[0]
    if (!file) return
    onImageSelect(file)
    // Reset file input so same file can be selected again
    e.target.value = ""
  }

  return (
    <div className="px-4 py-3 border-t border-gray-200 flex items-center gap-2">

      {/* Hidden file input */}
      <input
        type="file"
        accept="image/*"
        ref={fileRef}
        onChange={handleFileChange}
        className="hidden"
      />

      {/* Image upload button */}
      <button
        onClick={() => fileRef.current.click()}
        className="text-green-600 hover:text-green-800 text-xl p-2 rounded-full hover:bg-green-50 transition"
        title="फसल की फोटो भेजें"
      >
        📷
      </button>

      {/* Text input */}
      <input
        type="text"
        value={input}
        onChange={(e) => onInputChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="अपना सवाल यहाँ लिखें..."
        disabled={loading}
        className="flex-1 border border-gray-300 rounded-full px-4 py-2 text-sm focus:outline-none focus:border-green-500 disabled:opacity-50"
      />

      {/* Send button */}
      <button
        onClick={onSend}
        disabled={loading}
        className="bg-green-600 hover:bg-green-700 active:bg-green-800 text-white rounded-full px-4 py-2 text-sm font-medium disabled:opacity-50 transition"
      >
        भेजें
      </button>

    </div>
  )
}

export default InputBar