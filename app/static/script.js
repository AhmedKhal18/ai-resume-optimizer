const form = document.querySelector("#optimizer-form");
const submitButton = document.querySelector("#submit-button");
const loadingMessage = document.querySelector("#loading-message");
const successMessage = document.querySelector("#success-message");
const errorMessage = document.querySelector("#error-message");
const results = document.querySelector("#results");
const resumeText = document.querySelector("#resume-text");
const resumePdf = document.querySelector("#resume-pdf");
const fileName = document.querySelector("#file-name");
const formControls = form.querySelectorAll("textarea, input, button");

const professionalSummary = document.querySelector("#professional-summary");
const improvedBullets = document.querySelector("#improved-bullets");
const missingKeywords = document.querySelector("#missing-keywords");
const atsRecommendations = document.querySelector("#ats-recommendations");
const copyButtons = document.querySelectorAll("[data-copy-target]");

function setList(element, items) {
  element.innerHTML = "";

  items.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    element.appendChild(li);
  });
}

function setLoading(isLoading) {
  loadingMessage.hidden = !isLoading;
  submitButton.textContent = isLoading ? "Optimizing..." : "Optimize Resume";

  formControls.forEach((control) => {
    control.disabled = isLoading;
  });
}

function showSuccess(message) {
  successMessage.textContent = message;
  successMessage.hidden = false;
  errorMessage.hidden = true;
}

function showError(message) {
  errorMessage.textContent = message;
  errorMessage.hidden = false;
  successMessage.hidden = true;
}

function clearMessages() {
  successMessage.hidden = true;
  errorMessage.hidden = true;
}

function getCopyText(element) {
  if (element.tagName === "UL") {
    return Array.from(element.querySelectorAll("li"))
      .map((item) => item.textContent)
      .join("\n");
  }

  return element.textContent;
}

copyButtons.forEach((button) => {
  button.addEventListener("click", async () => {
    const target = document.querySelector(`#${button.dataset.copyTarget}`);
    const text = getCopyText(target).trim();

    if (!text) {
      return;
    }

    await navigator.clipboard.writeText(text);
    button.textContent = "Copied";

    setTimeout(() => {
      button.textContent = "Copy";
    }, 1400);
  });
});

resumePdf.addEventListener("change", () => {
  const file = resumePdf.files[0];
  fileName.textContent = file ? file.name : "No PDF selected.";
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const formData = new FormData(form);

  if (!resumeText.value.trim() && resumePdf.files.length === 0) {
    showError("Paste your resume text or upload a PDF resume.");
    results.hidden = true;
    return;
  }

  setLoading(true);
  clearMessages();
  results.hidden = true;

  try {
    const response = await fetch("/api/optimize-resume", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Something went wrong.");
    }

    professionalSummary.textContent = data.professional_summary;
    setList(improvedBullets, data.improved_bullets || []);
    setList(missingKeywords, data.missing_keywords || []);
    setList(atsRecommendations, data.ats_recommendations || []);

    results.hidden = false;
    showSuccess("Resume optimization complete. Your results are ready below.");
    results.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    showError(error.message);
  } finally {
    setLoading(false);
  }
});
