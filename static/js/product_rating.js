document.addEventListener('DOMContentLoaded', function() {
    const ratingStarsContainer = document.querySelector('.rating-stars-visual');
    const ratingStars = document.querySelectorAll('.rating-star-visual');
    const ratingRadios = document.querySelectorAll('input[name="rating"]');

    function updateStars(selectedValue) {
        ratingStars.forEach(star => {
            const starValue = parseInt(star.dataset.value, 10);
            if (starValue <= selectedValue) {
                star.classList.add('selected');
            } else {
                star.classList.remove('selected');
            }
        });
    }

    if (ratingStarsContainer) {
        ratingStarsContainer.addEventListener('click', function(e) {
            if (e.target && e.target.matches('.rating-star-visual')) {
                const value = e.target.dataset.value;
                const correspondingRadio = document.querySelector(`input[name="rating"][value="${value}"]`);
                if (correspondingRadio) {
                    correspondingRadio.checked = true;
                    correspondingRadio.dispatchEvent(new Event('change'));
                }
            }
        });

        ratingStarsContainer.addEventListener('keydown', function(e) {
            if (e.target && e.target.matches('.rating-star-visual') && (e.key === 'Enter' || e.key === ' ')) {
                e.preventDefault();
                const value = e.target.dataset.value;
                const correspondingRadio = document.querySelector(`input[name="rating"][value="${value}"]`);
                if (correspondingRadio) {
                    correspondingRadio.checked = true;
                    correspondingRadio.dispatchEvent(new Event('change'));
                }
            }
        });
    }

    if (ratingRadios.length > 0) {
        ratingRadios.forEach(radio => {
            radio.addEventListener('change', function() {
                if (this.checked) updateStars(parseInt(this.value, 10));
            });

            if (radio.checked) updateStars(parseInt(radio.value, 10));
        });

        const anyChecked = Array.from(ratingRadios).some(radio => radio.checked);
        if (!anyChecked) updateStars(0);
    }
});