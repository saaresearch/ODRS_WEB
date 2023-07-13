// Обработка кликов на элементы выпадающего списка
document.addEventListener("DOMContentLoaded", function() {
    var dropdownBtns = document.querySelectorAll(".dropdown-btn");

    dropdownBtns.forEach(function(btn) {
        btn.addEventListener("click", function() {
            this.parentNode.querySelector(".dropdown-content").classList.toggle("show");
        });
    });

    // Закрытие выпадающего списка при клике вне его области
    window.addEventListener("click", function(event) {
        if (!event.target.matches(".dropdown-btn")) {
            var dropdowns = document.querySelectorAll(".dropdown-content");
            dropdowns.forEach(function(dropdown) {
                if (dropdown.classList.contains("show")) {
                    dropdown.classList.remove("show");
                }
            });
        }
    });
});