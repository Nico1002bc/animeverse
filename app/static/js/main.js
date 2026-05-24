/* AniVerse – main.js */

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".flash").forEach(flash => {
    setTimeout(() => {
      flash.style.transition = "opacity 0.5s ease, transform 0.5s ease";
      flash.style.opacity = "0";
      flash.style.transform = "translateY(-8px)";
      setTimeout(() => flash.remove(), 500);
    }, 4000);
  });
});
