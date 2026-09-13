const API_BASE =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export async function sendChatMessage(question, history = []) {
  const response = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question,
      history,
    }),
  });

  if (!response.ok) {
    let errorMessage = `API request failed: ${response.status}`;

    try {
      const errorData = await response.json();

      if (typeof errorData?.error === "string") {
        errorMessage = errorData.error;
      }
    } catch {
      // Keep the fallback error message if the response
      // does not contain valid JSON.
    }

    const error = new Error(errorMessage);
    error.status = response.status;
    throw error;
  }

  const data = await response.json();

  return {
    ...data,
    answer: data.answer ?? data.response,
  };
}