function handleKey(event) {
    if (event.key === "Enter") {
        sendMessage();
    }
}

// 🔥 Typing animation function
function typeText(element, text, speed = 20) {
    let i = 0;
    element.innerHTML = "";

    function typing() {
        if (i < text.length) {
            element.innerHTML += text.charAt(i);
            i++;
            setTimeout(typing, speed);
        }
    }

    typing();
}

async function sendMessage() {
    const input = document.getElementById("user-input");
    const chatBox = document.getElementById("chat-box");

    const message = input.value.trim();
    if (!message) return;

    // Show user message
    chatBox.innerHTML += `<div class="user">${message}</div>`;
    input.value = "";

    // Typing placeholder
    const typingDiv = document.createElement("div");
    typingDiv.className = "bot";
    typingDiv.innerHTML = "Typing...";
    chatBox.appendChild(typingDiv);

    chatBox.scrollTop = chatBox.scrollHeight;

    const res = await fetch("/chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ text: message })
    });

    const data = await res.json();

    // Clear typing text
    typingDiv.innerHTML = "";

    // 🔥 Animate response
    typeText(typingDiv, data.response);

    chatBox.scrollTop = chatBox.scrollHeight;
}