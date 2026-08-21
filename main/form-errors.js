const ERROR_MARKERS = [
    "Invalid data",
    "Invalid code",
    "Неверный пароль",
    "Пользователь не найден",
    "Пользователь с таким email уже есть",
    "Нет такого пользователя",
];

const form = document.querySelector("[data-ajax-form]");
const widget = document.getElementById("error-widget");
const errorList = document.getElementById("error-list");
const closeButton = document.getElementById("close-errors");
const submitButton = form.querySelector('[type="submit"]');

function responseToText(responseBody) {
    return new DOMParser()
        .parseFromString(responseBody, "text/html")
        .body.textContent.trim();
}

function showError(message) {
    const item = document.createElement("li");
    item.textContent = message;

    errorList.replaceChildren(item);
    widget.hidden = false;
    closeButton.focus();
}

function closeWidget() {
    widget.hidden = true;
    form.querySelector("input")?.focus();
}

function prepareCodeInput() {
    if (form.dataset.formKind !== "code") {
        return null;
    }

    const codeInput = form.elements.us_code;
    codeInput.addEventListener("input", () => {
        codeInput.value = codeInput.value.replace(/\D/g, "").slice(0, 6);
    });

    return codeInput;
}

const codeInput = prepareCodeInput();

closeButton.addEventListener("click", closeWidget);

widget.addEventListener("click", (event) => {
    if (event.target === widget) {
        closeWidget();
    }
});

document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !widget.hidden) {
        closeWidget();
    }
});

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (codeInput && !/^\d{6}$/.test(codeInput.value)) {
        showError("Введите код из 6 цифр.");
        return;
    }

    submitButton.disabled = true;

    try {
        const response = await fetch(form.action || window.location.href, {
            method: "POST",
            body: new FormData(form),
            credentials: "same-origin",
        });
        const responseBody = await response.text();
        const responseText = responseToText(responseBody);

        if (!response.ok) {
            showError("Не удалось обработать запрос. Попробуйте ещё раз.");
        } else if (ERROR_MARKERS.some((marker) => responseText.includes(marker))) {
            const message = responseText === "Invalid code"
                ? "Введён неверный код подтверждения."
                : responseText;
            showError(message);
        } else if (response.redirected) {
            window.location.assign(response.url);
        } else {
            document.open();
            document.write(responseBody);
            document.close();
        }
    } catch (error) {
        showError("Нет связи с сервером. Попробуйте ещё раз.");
    } finally {
        submitButton.disabled = false;
    }
});
