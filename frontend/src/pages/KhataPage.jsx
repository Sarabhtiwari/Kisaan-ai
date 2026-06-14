import { useState, useEffect } from "react";
import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api"
const API = axios.create({ baseURL: BASE_URL })
// Get session ID from localStorage
function getSessionId() {
  return localStorage.getItem("kisaan_session_id") || "";
}

function KhataPage() {
  const [farms, setFarms] = useState([]);
  const [selectedFarm, setSelectedFarm] = useState(null);
  const [expenses, setExpenses] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [response, setResponse] = useState("");

  const sessionId = getSessionId();

  // Load farms on page load
  useEffect(() => {
    loadFarms();
  }, []);

  // Load expenses when farm changes
  useEffect(() => {
    if (selectedFarm) {
      loadExpenses(selectedFarm);
      loadSummary(selectedFarm);
    }
  }, [selectedFarm]);

  async function loadFarms() {
    try {
      setLoading(true);
      const res = await API.get(`/khata/farms?session_id=${sessionId}`);
      setFarms(res.data.farms || []);
      if (res.data.farms?.length > 0) {
        setSelectedFarm(res.data.farms[0]);
      }
    } catch (e) {
      console.error("Error loading farms:", e);
    } finally {
      setLoading(false);
    }
  }

  async function loadExpenses(farmName) {
    try {
      const res = await API.get(
        `/khata/expenses?session_id=${sessionId}&farm_name=${farmName}`,
      );
      setExpenses(res.data.expenses || []);
    } catch (e) {
      console.error("Error loading expenses:", e);
    }
  }

  async function loadSummary(farmName) {
    try {
      const res = await API.get(
        `/khata/summary?session_id=${sessionId}&farm_name=${farmName}`,
      );
      setSummary(res.data);
    } catch (e) {
      console.error("Error loading summary:", e);
    }
  }

  async function handleSend() {
    if (!input.trim()) return;
    setSending(true);
    setResponse("");

    try {
      const sessionId = getSessionId();

      // Use fetch with streaming same as ChatPage
      const res = await fetch(`${BASE_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          message: input,
          language: "hi",
          image_base64: null,
          location: { city: "Lucknow" },
        }),
      });

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let fullReply = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const text = decoder.decode(value);
        const lines = text.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.type === "chunk") {
                fullReply += data.content;
                setResponse(fullReply); // update as words arrive
              }
            } catch (e) {}
          }
        }
      }

      // Refresh data after response
      await loadFarms();
      if (selectedFarm) {
        await loadExpenses(selectedFarm);
        await loadSummary(selectedFarm);
      }
    } catch (e) {
      setResponse("Error. Please try again.");
    } finally {
      setSending(false);
      setInput("");
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter") handleSend();
  }

  return (
    <div className="max-w-2xl mx-auto p-4 space-y-4">
      {/* Page Title */}
      <div className="bg-white rounded-2xl p-4 shadow-sm border border-green-100">
        <h2 className="text-lg font-bold text-green-800">📒 किसान खाता</h2>
        <p className="text-sm text-gray-500">अपने खेतों का हिसाब-किताब रखें</p>
      </div>

      {/* Quick Add Input */}
      <div className="bg-white rounded-2xl p-4 shadow-sm border border-green-100">
        <p className="text-sm text-gray-600 mb-2 font-medium">
          नया खर्चा या आमदनी दर्ज करें:
        </p>
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="जैसे: कhet 1 mein 2500 ka paani lagaya"
            className="flex-1 border border-gray-300 rounded-full px-4 py-2 text-sm focus:outline-none focus:border-green-500"
          />
          <button
            onClick={handleSend}
            disabled={sending}
            className="bg-green-600 hover:bg-green-700 text-white rounded-full px-4 py-2 text-sm font-medium disabled:opacity-50"
          >
            {sending ? "..." : "दर्ज करें"}
          </button>
        </div>

        {/* AI Response */}
        {response && (
          <div className="mt-3 p-3 bg-green-50 rounded-xl text-sm text-green-800">
            🌾 {response}
          </div>
        )}
      </div>

      {/* Farm Tabs */}
      {farms.length > 0 && (
        <div className="bg-white rounded-2xl p-4 shadow-sm border border-green-100">
          <p className="text-sm font-medium text-gray-600 mb-2">खेत चुनें:</p>
          <div className="flex gap-2 flex-wrap">
            {farms.map((farm) => (
              <button
                key={farm}
                onClick={() => setSelectedFarm(farm)}
                className={`px-4 py-1.5 rounded-full text-sm font-medium transition ${
                  selectedFarm === farm
                    ? "bg-green-600 text-white"
                    : "bg-gray-100 text-gray-700 hover:bg-green-50"
                }`}
              >
                🌱 {farm}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-white rounded-2xl p-4 shadow-sm border border-red-100 text-center">
            <p className="text-xs text-gray-500 mb-1">कुल खर्चा</p>
            <p className="text-lg font-bold text-red-600">
              ₹{summary.total_expense?.toLocaleString() || 0}
            </p>
          </div>
          <div className="bg-white rounded-2xl p-4 shadow-sm border border-green-100 text-center">
            <p className="text-xs text-gray-500 mb-1">कुल आमदनी</p>
            <p className="text-lg font-bold text-green-600">
              ₹{summary.total_income?.toLocaleString() || 0}
            </p>
          </div>
          <div
            className={`bg-white rounded-2xl p-4 shadow-sm text-center border ${
              (summary.net_profit || 0) >= 0
                ? "border-green-100"
                : "border-red-100"
            }`}
          >
            <p className="text-xs text-gray-500 mb-1">नफा / नुकसान</p>
            <p
              className={`text-lg font-bold ${
                (summary.net_profit || 0) >= 0
                  ? "text-green-700"
                  : "text-red-600"
              }`}
            >
              ₹{summary.net_profit?.toLocaleString() || 0}
            </p>
          </div>
        </div>
      )}

      {/* Category Breakdown */}
      {summary?.category_breakdown &&
        Object.keys(summary.category_breakdown).length > 0 && (
          <div className="bg-white rounded-2xl p-4 shadow-sm border border-green-100">
            <p className="text-sm font-medium text-gray-700 mb-3">
              श्रेणी अनुसार खर्चा:
            </p>
            <div className="space-y-2">
              {Object.entries(summary.category_breakdown).map(([cat, amt]) => (
                <div key={cat} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 capitalize">
                    {cat}
                  </span>
                  <span className="text-sm font-medium text-gray-800">
                    ₹{Number(amt).toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

      {/* Expense Table */}
      {expenses.length > 0 && (
        <div className="bg-white rounded-2xl p-4 shadow-sm border border-green-100">
          <p className="text-sm font-medium text-gray-700 mb-3">
            {selectedFarm} — सभी entries ({expenses.length})
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left py-2 text-gray-500 font-medium">
                    तारीख
                  </th>
                  <th className="text-left py-2 text-gray-500 font-medium">
                    श्रेणी
                  </th>
                  <th className="text-left py-2 text-gray-500 font-medium">
                    विवरण
                  </th>
                  <th className="text-right py-2 text-gray-500 font-medium">
                    राशि
                  </th>
                </tr>
              </thead>
              <tbody>
                {expenses.map((exp, i) => (
                  <tr
                    key={i}
                    className="border-b border-gray-50 hover:bg-gray-50"
                  >
                    <td className="py-2 text-gray-600">
                      {new Date(exp.expense_date).toLocaleDateString("hi-IN")}
                    </td>
                    <td className="py-2">
                      <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded-full text-xs">
                        {exp.category}
                      </span>
                    </td>
                    <td className="py-2 text-gray-600">{exp.purpose}</td>
                    <td
                      className={`py-2 text-right font-medium ${
                        exp.is_income ? "text-green-600" : "text-red-600"
                      }`}
                    >
                      {exp.is_income ? "+" : "-"}₹
                      {Number(exp.amount).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Empty state */}
      {farms.length === 0 && !loading && (
        <div className="bg-white rounded-2xl p-8 shadow-sm border border-green-100 text-center">
          <p className="text-4xl mb-3">🌱</p>
          <p className="text-gray-600 font-medium">अभी कोई खेत नहीं है</p>
          <p className="text-gray-400 text-sm mt-1">
            ऊपर बॉक्स में लिखें: "khet 1 mein 2500 ka paani lagaya"
          </p>
        </div>
      )}
    </div>
  );
}

export default KhataPage;
