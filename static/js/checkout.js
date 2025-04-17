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

    quantityInputs.forEach(input => {
        input.addEventListener('input', calculateAndUpdateTotals);
    });

    deliveryRadios.forEach(radio => {
        radio.addEventListener('change', calculateAndUpdateTotals);
    });

    calculateAndUpdateTotals();

    form.addEventListener("submit", function (event) {
        const invalidFields = form.querySelectorAll(":invalid");

        if (invalidFields.length > 0) {
            event.preventDefault();
            invalidFields.forEach(field => {
                field.classList.add("is-invalid");
            });

            invalidFields[0].scrollIntoView({ behavior: "smooth", block: "center" });
        }
    });

    form.querySelectorAll("input, select, textarea").forEach(field => {
        field.addEventListener("input", () => {
            if (field.checkValidity()) {
                field.classList.remove("is-invalid");
            }
        });
        field.addEventListener("change", () => {
            if (field.checkValidity()) {
                field.classList.remove("is-invalid");
            }
        });
    });
});