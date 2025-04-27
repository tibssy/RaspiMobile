/**
 * @file product_rating.js
 * @description Handles the interactive star rating input in the product review form.
 * It synchronizes the visual appearance of star elements (full/empty) with the
 * underlying radio button selection, allowing users to click stars to select a rating.
 * It also ensures keyboard accessibility for the star rating interaction.
 */

document.addEventListener("DOMContentLoaded", function () {
    const ratingStarsContainer = document.querySelector(".rating-stars-visual");
    const ratingStars = document.querySelectorAll(".rating-star-visual");
    const ratingRadios = document.querySelectorAll('input[name="rating"]');

    /**
     * Updates the visual state (CSS class 'selected') of the star elements
     * based on the currently selected rating value. Stars up to the selected
     * value will have the 'selected' class, others will not.
     *
     * @param {number} selectedValue - The rating value that is currently selected (e.g., 1, 2, 3, 4, 5).
     *                                  Pass 0 to clear all selections visually.
     */
    function updateStars(selectedValue) {
        ratingStars.forEach((star) => {
            const starValue = parseInt(star.dataset.value, 10);
            if (starValue <= selectedValue) {
                star.classList.add("selected");
            } else {
                star.classList.remove("selected");
            }
        });
    }

    // Add listeners to the visual star container for click and keyboard events
    if (ratingStarsContainer) {
        ratingStarsContainer.addEventListener("click", function (e) {
            if (e.target && e.target.matches(".rating-star-visual")) {
                const value = e.target.dataset.value;
                const correspondingRadio = document.querySelector(
                    `input[name="rating"][value="${value}"]`
                );
                if (correspondingRadio) {
                    correspondingRadio.checked = true;
                    correspondingRadio.dispatchEvent(new Event("change"));
                }
            }
        });

        /**
         * Handles keydown events (Enter or Space) on the visual stars container
         * for keyboard accessibility. If a star element has focus and Enter/Space
         * is pressed, it checks the corresponding radio button.
         */
        ratingStarsContainer.addEventListener("keydown", function (e) {
            if (
                e.target &&
                e.target.matches(".rating-star-visual") &&
                (e.key === "Enter" || e.key === " ")
            ) {
                e.preventDefault();
                const value = e.target.dataset.value;
                const correspondingRadio = document.querySelector(
                    `input[name="rating"][value="${value}"]`
                );
                if (correspondingRadio) {
                    correspondingRadio.checked = true;
                    correspondingRadio.dispatchEvent(new Event("change"));
                }
            }
        });
    }

    // Add listeners to the actual radio buttons
    if (ratingRadios.length > 0) {
        ratingRadios.forEach((radio) => {
            radio.addEventListener("change", function () {
                if (this.checked) updateStars(parseInt(this.value, 10));
            });

            if (radio.checked) updateStars(parseInt(radio.value, 10));
        });

        const anyChecked = Array.from(ratingRadios).some(
            (radio) => radio.checked
        );
        if (!anyChecked) updateStars(0);
    }
});
