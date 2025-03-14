async function fetchStreamingResponse(user_id, query) {
    const response = await fetch("/chat_api/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id, query })
    });

    if (!response.body) return;

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");

    let result = "";

    while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true }).trim();
        // 🔥 SSE 형식 처리 (줄 단위 파싱)
        const lines = chunk.split("\n\n");  
        for (let line of lines) {
            if (line.startsWith("data:")) {
                try {
                    const data = JSON.parse(line.slice(5));  // "data: " 제거 후 JSON 파싱
                    result += data.response;
                    
                    // ✅ UI 실시간 업데이트
                    document.getElementById("chatBox").innerHTML += `<div class="chat-message ai"><div class="message">${data.response}</div></div>`;
                } catch (e) {
                    console.error("JSON 파싱 오류:", e, "데이터:", line);
                }
            }
        }
    }

    console.log("Final Response:", result);
}
