document.addEventListener("DOMContentLoaded", () => {
  const forms = document.querySelectorAll("form[data-show-progress]");
  forms.forEach((form) => {
    const messageText = form.getAttribute("data-progress-message") || "Processing…";
    let messageNode;

    form.addEventListener("submit", (event) => {
      if (form.classList.contains("is-submitting")) return;
      form.classList.add("is-submitting");

      const submitButtons = form.querySelectorAll("button[type='submit'], input[type='submit']");
      submitButtons.forEach((button) => {
        button.classList.add("is-loading");
        button.setAttribute("disabled", "disabled");
      });

      messageNode = document.createElement("div");
      messageNode.className = "form-progress";
      messageNode.innerHTML = `
        <span class="spinner" aria-hidden="true"></span>
        <span>${messageText}</span>
      `;
      form.appendChild(messageNode);
    });
  });
});
