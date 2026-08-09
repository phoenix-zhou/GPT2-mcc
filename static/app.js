const form = document.querySelector("#consultation-form");
const submitButton = document.querySelector("#submit-button");

if (form && submitButton) {
    form.addEventListener("submit", () => {
        submitButton.disabled = true;
        submitButton.classList.add("is-loading");
        const label = submitButton.querySelector(".button-label");
        if (label) label.textContent = "正在生成，请稍候…";
    });
}
