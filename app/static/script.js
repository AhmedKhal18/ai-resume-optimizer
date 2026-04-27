const form = document.querySelector("#optimizer-form");
const submitButton = document.querySelector("#submit-button");
const loadingMessage = document.querySelector("#loading-message");
const errorMessage = document.querySelector("#error-message");
const results = document.querySelector("#results");

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
  submitButton.disabled = isLoading;
  submitButton.textContent = isLoading ? "Optimizing..." : "Optimize Resume";
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

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const formData = new FormData(form);
  const payload = {
    resume_text: formData.get("resume_text"),
    job_description: formData.get("job_description"),
  };

  setLoading(true);
  errorMessage.hidden = true;
  results.hidden = true;

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
      throw new Error(data.detail || "Something went wrong.");
    }

    professionalSummary.textContent = data.professional_summary;
    setList(improvedBullets, data.improved_bullets || []);
    setList(missingKeywords, data.missing_keywords || []);
    setList(atsRecommendations, data.ats_recommendations || []);

    results.hidden = false;
  } catch (error) {
    errorMessage.textContent = error.message;
    errorMessage.hidden = false;
  } finally {
    setLoading(false);
  }
});
