const form = document.querySelector("#optimizer-form");
const submitButton = document.querySelector("#submit-button");
const loadingMessage = document.querySelector("#loading-message");
const successMessage = document.querySelector("#success-message");
const errorMessage = document.querySelector("#error-message");
const results = document.querySelector("#results");
const downloadResultsButton = document.querySelector("#download-results");
const resumeText = document.querySelector("#resume-text");
const resumePdf = document.querySelector("#resume-pdf");
const jobDescription = document.querySelector("#job-description");
const fileName = document.querySelector("#file-name");
const formControls = form.querySelectorAll("textarea, input, button");

const professionalSummary = document.querySelector("#professional-summary");
const matchScore = document.querySelector("#match-score");
const matchScoreBar = document.querySelector("#match-score-bar");
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
  submitButton.textContent = isLoading ? "Analyzing..." : "Optimize Resume";

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
  errorMessage.textContent = getFriendlyMessage(message);
  errorMessage.hidden = false;
  successMessage.hidden = true;
}

function clearMessages() {
  successMessage.hidden = true;
  errorMessage.hidden = true;
}

function getFriendlyMessage(value) {
  if (value instanceof Error) {
    return value.message || "Something went wrong. Please try again.";
  }

  if (typeof value === "string") {
    return value;
  }

  if (Array.isArray(value)) {
    const messages = value
      .map((item) => item.msg || item.message)
      .filter(Boolean);

    return messages.length
      ? messages.join(" ")
      : "Please check your inputs and try again.";
  }

  if (value && typeof value === "object") {
    return value.message || value.detail || "Something went wrong. Please try again.";
  }

  return "Something went wrong. Please try again.";
}

function getErrorMessage(detail) {
  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => item.msg || item.message)
      .filter(Boolean)
      .join(" ");
  }

  if (detail && typeof detail === "object") {
    return detail.message || detail.detail || "Something went wrong. Please try again.";
  }

  return "Something went wrong. Please try again.";
}

function validateForm() {
  const hasResumeText = resumeText.value.trim().length > 0;
  const hasResumePdf = resumePdf.files.length > 0;
  const hasJobDescription = jobDescription.value.trim().length > 0;

  if (!hasResumeText && !hasResumePdf) {
    return {
      message: "Please paste your resume text or upload a PDF resume.",
      field: resumeText,
    };
  }

  if (!hasJobDescription) {
    return {
      message: "Please paste the job description before optimizing your resume.",
      field: jobDescription,
    };
  }

  return null;
}

function getCopyText(element) {
  if (element.tagName === "UL") {
    return Array.from(element.querySelectorAll("li"))
      .map((item) => item.textContent)
      .join("\n");
  }

  return element.textContent;
}

function buildResultsText() {
  return [
    "AI Resume Optimizer Results",
    "",
    `Match Score: ${matchScore.textContent}`,
    "",
    "Professional Summary",
    professionalSummary.textContent.trim(),
    "",
    "Improved Resume Bullets",
    getCopyText(improvedBullets),
    "",
    "Missing Keywords",
    getCopyText(missingKeywords),
    "",
    "ATS Recommendations",
    getCopyText(atsRecommendations),
  ].join("\n");
}

function downloadResults() {
  const blob = new Blob([buildResultsText()], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.download = "ai-resume-optimizer-results.txt";
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
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

downloadResultsButton.addEventListener("click", downloadResults);

resumePdf.addEventListener("change", () => {
  const file = resumePdf.files[0];
  fileName.textContent = file ? file.name : "No PDF selected.";
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearMessages();
  results.hidden = true;

  const validationError = validateForm();
  if (validationError) {
    showError(validationError.message);
    results.hidden = true;
    validationError.field.focus();
    return;
  }

  const payload = {
    resume_text: resumeText.value.trim(),
    job_description: jobDescription.value.trim(),
  };

  setLoading(true);

  try {
    const response = await fetch("/api/optimize-resume", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    if (!response.ok) {
      showError(getErrorMessage(data.detail));
      return;
    }

    const score = Math.max(0, Math.min(100, data.match_score || 0));
    matchScore.textContent = `${score}%`;
    matchScoreBar.style.width = `${score}%`;
    professionalSummary.textContent = data.professional_summary;
    setList(improvedBullets, data.improved_bullets || []);
    setList(missingKeywords, data.missing_keywords || []);
    setList(atsRecommendations, data.ats_recommendations || []);

    results.hidden = false;
    showSuccess("Resume optimization complete. Your results are ready below.");
    results.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    showError(error);
  } finally {
    setLoading(false);
  }
});
