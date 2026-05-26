/* AniVerse – main.js */

document.addEventListener("DOMContentLoaded", () => {
  // Flash auto-close
  document.querySelectorAll(".flash").forEach(flash => {
    setTimeout(() => {
      flash.style.transition = "opacity 0.5s ease, transform 0.5s ease";
      flash.style.opacity = "0";
      flash.style.transform = "translateY(-8px)";
      setTimeout(() => flash.remove(), 500);
    }, 4000);
  });

  // Preview imagen URL (crear/editar anime)
  const imgInput = document.getElementById("imagen_url");
  const imgPreview = document.getElementById("img-preview");
  if (imgInput && imgPreview) {
    const updatePreview = () => {
      const url = imgInput.value.trim();
      if (url) {
        imgPreview.src = url;
        imgPreview.style.display = "block";
        imgPreview.onerror = () => { imgPreview.style.display = "none"; };
      } else {
        imgPreview.style.display = "none";
      }
    };
    imgInput.addEventListener("input", updatePreview);
    if (imgInput.value) updatePreview();
  }

  // Modal confirmación (borrar anime)
  const modal = document.getElementById("confirm-modal");
  if (modal) {
    let targetForm = null;
    document.querySelectorAll("[data-confirm]").forEach(btn => {
      btn.addEventListener("click", e => {
        e.preventDefault();
        document.getElementById("confirm-msg").textContent = btn.dataset.confirm || "¿Estás seguro?";
        targetForm = btn.closest("form");
        modal.classList.add("active");
      });
    });
    document.getElementById("confirm-yes")?.addEventListener("click", () => {
      if (targetForm) targetForm.submit();
    });
    document.getElementById("confirm-no")?.addEventListener("click", () => {
      modal.classList.remove("active");
    });
    modal.addEventListener("click", e => {
      if (e.target === modal) modal.classList.remove("active");
    });
  }
});
