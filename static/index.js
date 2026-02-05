
const urls_list = document.getElementById('url_list');

let timeoutId = null;
const DELAY_MS = 1000;

urls_list.addEventListener("input", () => {

    if (timeoutId !== null) {
        clearTimeout(timeoutId);
    }

    timeoutId = setTimeout(() => {
        sendText(urls_list.value);
    }, DELAY_MS);

});

async function sendText(text) {
    try {
        const response = await fetch("/projects", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ text }),
        });

        if (response.ok) {
            // Сервер вернул 200-299
            urls_list.style.backgroundColor = "lightgreen"; // успешный ответ
        } else if (response.status === 422) {
            // Валидатор Pydantic вернул ошибку
            urls_list.style.backgroundColor = "lightcoral"; // ошибка валидации
        } else {
            urls_list.style.backgroundColor = "lightyellow"; // другие ошибки
        }

    } catch (err) {
        console.error("Ошибка сети:", err);
    }
}