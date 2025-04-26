document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('checkout-form');
    const deliveryCostEl = document.getElementById('delivery-cost');
    const subtotalEl = document.getElementById('cart-subtotal');
    const grandTotalEl = document.getElementById('grand-total');
    const quantityInputs = form.querySelectorAll('.quantity-input');
    const itemSubtotalEls = form.querySelectorAll('.item-subtotal');
    const deliveryRadios = form.querySelectorAll('input[name="delivery-delivery_method"]');

    let deliveryCosts = {};
    try {
        const deliveryCostsDataElement = document.getElementById('delivery-costs-data');
        if (deliveryCostsDataElement) {
            deliveryCosts = JSON.parse(deliveryCostsDataElement.textContent);
        } else {
            console.error("Delivery costs data element not found!");
        }
    } catch (e) {
        console.error("Error parsing delivery costs data:", e);
    }

    function calculateAndUpdateTotals() {
        let currentSubtotal = 0;

        quantityInputs.forEach((input, index) => {
            const quantity = parseInt(input.value) || 0;
            const itemSubtotalEl = itemSubtotalEls[index];

            if (itemSubtotalEl && itemSubtotalEl.dataset.price) {
                const price = parseFloat(itemSubtotalEl.dataset.price) || 0;
                const itemTotal = quantity * price;
                itemSubtotalEl.textContent = '€' + itemTotal.toFixed(2);

                currentSubtotal += itemTotal;
            } else {
                console.warn(`Missing price or subtotal element for quantity input at index ${index}`);
            }
        });

        subtotalEl.textContent = '€' + currentSubtotal.toFixed(2);

        let deliveryCost = 0;
        const selectedDelivery = form.querySelector('input[name="delivery-delivery_method"]:checked');

        if (selectedDelivery && deliveryCosts && deliveryCosts[selectedDelivery.value]) {
            deliveryCost = parseFloat(deliveryCosts[selectedDelivery.value]) || 0;
        }

        deliveryCostEl.textContent = '€' + deliveryCost.toFixed(2);
        const grandTotal = currentSubtotal + deliveryCost;
        grandTotalEl.textContent = '€' + grandTotal.toFixed(2);
    }

    function validateStock(quantityInput) {
        const rawValue = quantityInput.value.trim();
        const quantity = Number(rawValue);
        const maxStock = parseInt(quantityInput.getAttribute('max'), 10);
        const minStock = parseInt(quantityInput.getAttribute('min'), 10) || 1;
        const errorContainer = quantityInput.closest('.col-7').querySelector('.client-stock-error');
        let isValid = true;
        let errorMessage = '';

        if (!errorContainer) {
            console.warn("Could not find client-stock-error container for input:", quantityInput);
            return true;
        }

        if (quantityInput.validity && quantityInput.validity.badInput) {
            errorMessage = 'Please enter a valid number.';
            isValid = false;
        } else if (!Number.isInteger(quantity)) {
            if (rawValue !== '') {
                errorMessage = 'Please enter a whole number.';
                isValid = false;
            }
        } else if (quantity < minStock) {
            errorMessage = `Quantity must be at least ${minStock}.`;
            isValid = false;
        } else if (isValid) {
            if (isNaN(maxStock)) {
                console.warn("Max stock attribute is missing or invalid for input:", quantityInput);
            } else if (quantity > maxStock) {
                errorMessage = `Max available: ${maxStock}`;
                isValid = false;
            }
        }

        if (!isValid) {
            quantityInput.classList.add('is-invalid');
            errorContainer.textContent = errorMessage;
            errorContainer.style.display = 'block';
        } else {
            quantityInput.classList.remove('is-invalid');
            errorContainer.textContent = '';
            errorContainer.style.display = 'none';
        }

        return isValid;
    }

    quantityInputs.forEach(input => {
        input.addEventListener('input', function() {
            validateStock(this);
            calculateAndUpdateTotals();
        });
        validateStock(input);
    });

    deliveryRadios.forEach(radio => {
        radio.addEventListener('change', calculateAndUpdateTotals);
    });

    calculateAndUpdateTotals();

    form.addEventListener("submit", function (event) {
        let formIsValid = true;

        quantityInputs.forEach(input => {
            if (!validateStock(input)) {
                formIsValid = false;
            }
        });

        const html5InvalidFields = form.querySelectorAll(":invalid");
        if (html5InvalidFields.length > 0) {
             formIsValid = false;
        }

        if (!formIsValid) {
            event.preventDefault();

            html5InvalidFields.forEach(field => {
                if (!field.classList.contains('is-invalid')) {
                    field.classList.add("is-invalid");
                }
            });

            const firstInvalid = form.querySelector(".is-invalid, :invalid");
            if (firstInvalid) {
                firstInvalid.scrollIntoView({ behavior: "smooth", block: "center" });
                // Optionally focus it
                 firstInvalid.focus();
            }
             console.log("Checkout form validation failed (client-side).");
        }
    });

    form.querySelectorAll("input, select, textarea").forEach(field => {
        field.addEventListener("input", () => {
            if (field.classList.contains('quantity-input')) {
                validateStock(field);
            } else if (field.checkValidity()) {
                field.classList.remove("is-invalid");
            }
        });

        field.addEventListener("change", () => {
            if (field.classList.contains('quantity-input')) {
                validateStock(field);
            } else if (field.checkValidity()) {
                field.classList.remove("is-invalid");
            }
        });
    });
});