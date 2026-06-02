import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom"
import ChatPage from "./pages/ChatPage"
import KhataPage from "./pages/KhataPage"

// Navigation bar shown on all pages
function NavBar() {
  const location = useLocation()

  return (
    <div className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-200 px-4 py-2 flex items-center justify-between max-w-2xl mx-auto">
      <span className="text-green-700 font-bold text-lg">🌾 किसान AI</span>
      <div className="flex gap-2">
        <Link
          to="/"
          className={`px-4 py-1.5 rounded-full text-sm font-medium transition ${
            location.pathname === "/"
              ? "bg-green-600 text-white"
              : "text-green-700 hover:bg-green-50"
          }`}
        >
          💬 Chat
        </Link>
        <Link
          to="/khata"
          className={`px-4 py-1.5 rounded-full text-sm font-medium transition ${
            location.pathname === "/khata"
              ? "bg-green-600 text-white"
              : "text-green-700 hover:bg-green-50"
          }`}
        >
          📒 खाता
        </Link>
      </div>
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-green-50">
        <NavBar />
        <div className="pt-14">
          <Routes>
            <Route path="/"       element={<ChatPage />} />
            <Route path="/khata"  element={<KhataPage />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  )
}

export default App