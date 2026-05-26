function ImagePreview({ image, onRemove }) {
  if (!image) return null

  return (
    <div className="px-4 pb-2 flex items-center gap-3 border-t border-gray-100 pt-2">
      <img
        src={image}
        alt="preview"
        className="h-16 w-16 object-cover rounded-lg border-2 border-green-300"
      />
      <div>
        <p className="text-xs text-gray-500 mb-1">फसल की फोटो तैयार है</p>
        <button
          onClick={onRemove}
          className="text-red-500 text-xs font-medium hover:text-red-700"
        >
          ✕ हटाएं
        </button>
      </div>
    </div>
  )
}

export default ImagePreview