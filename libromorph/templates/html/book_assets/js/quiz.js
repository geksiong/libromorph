/**
 * quiz.js: Interactive Quiz Engine for LibroMorph HTML Reader.
 * Handles instant feedback, scoring, animations, explanations, and retry logic.
 */

document.addEventListener("DOMContentLoaded", function () {
  initQuizzes();
});

function initQuizzes() {
  const quizzes = document.querySelectorAll(".interactive-quiz");

  quizzes.forEach((quiz) => {
    const options = quiz.querySelectorAll(".quiz-option-btn");
    const feedback = quiz.querySelector(".quiz-feedback");
    const banner = quiz.querySelector(".quiz-feedback-banner");
    const retryBtn = quiz.querySelector(".quiz-retry-btn");

    options.forEach((btn) => {
      btn.addEventListener("click", function () {
        const isCorrect = btn.getAttribute("data-correct") === "true";

        // Disable all options in this quiz
        options.forEach((b) => {
          b.disabled = true;
          b.style.cursor = "default";
        });

        if (isCorrect) {
          btn.classList.add("is-correct");
          btn.querySelector(".quiz-status-icon").textContent = "✓";

          feedback.className = "quiz-feedback feedback-success";
          banner.innerHTML = "🎉 Correct! Outstanding work.";
          feedback.style.display = "block";
          if (retryBtn) retryBtn.style.display = "none";
        } else {
          btn.classList.add("is-wrong");
          btn.querySelector(".quiz-status-icon").textContent = "✗";

          // Highlight the right option for learning
          options.forEach((b) => {
            if (b.getAttribute("data-correct") === "true") {
              b.classList.add("is-correct");
              b.querySelector(".quiz-status-icon").textContent = "✓ (Correct)";
            }
          });

          feedback.className = "quiz-feedback feedback-failure";
          banner.innerHTML = "💡 Not quite right. Review the explanation below:";
          feedback.style.display = "block";
          if (retryBtn) retryBtn.style.display = "inline-block";
        }
      });
    });

    if (retryBtn) {
      retryBtn.addEventListener("click", function () {
        options.forEach((b) => {
          b.disabled = false;
          b.style.cursor = "pointer";
          b.classList.remove("is-correct", "is-wrong");
          b.querySelector(".quiz-status-icon").textContent = "";
        });
        feedback.style.display = "none";
        retryBtn.style.display = "none";
      });
    }
  });
}
