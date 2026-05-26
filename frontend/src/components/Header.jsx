function Header({ language, onLanguageChange }) {
  return (
    <div className="bg-green-600 text-white px-6 py-4 rounded-t-2xl flex items-center justify-between">
      <div>
        <h1 className="text-xl font-bold">🌾 किसान AI</h1>
        <p className="text-green-100 text-sm">आपका कृषि सहायक</p>
      </div>

      <select
        value={language}
        onChange={(e) => onLanguageChange(e.target.value)}
        className="bg-green-700 text-white text-sm rounded-lg px-3 py-1 border border-green-500"
      >
        <option value="hi">हिंदी</option>
        <option value="en">English</option>
        <option value="pa">ਪੰਜਾਬੀ</option>
        <option value="mr">मराठी</option>
        <option value="te">తెలుగు</option>
      </select>
    </div>
  )
}

export default Header