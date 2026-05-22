import axios from "axios"

const API = axios.create({
  baseURL: "http://127.0.0.1:8000/api",
  headers: {
    "Content-Type": "application/json"
  }
})

export async function sendMessage(message, language, imageBase64, location) {
  const response = await API.post("/chat", {
    session_id: "farmer_" + Math.random().toString(36).substr(2, 9),
    message: message,
    language: language || "hi",
    image_base64: imageBase64 || null,
    location: location || { city: "Lucknow" }
  })

  return response.data
}