document.addEventListener('DOMContentLoaded', function() {
    const stripePublicKey = JSON.parse(document.getElementById('id_stripe_public_key').textContent);
    const clientSecret = JSON.parse(document.getElementById('id_client_secret').textContent);
    const orderNumberElement = document.getElementById('order-number');
    const orderNumber = orderNumberElement ? orderNumberElement.dataset.orderNumber : null;
    const stripe = Stripe(stripePublicKey);

    const appearance = {
        theme: 'stripe',
    };
    const elements = stripe.elements({ appearance, clientSecret });

    const paymentElementOptions = {
        layout: "tabs",
    };
    const paymentElement = elements.create("payment", paymentElementOptions);
    paymentElement.mount("#payment-element");

    const form = document.getElementById('payment-form');
    const submitButton = document.getElementById('submit-button');
    const spinner = document.getElementById('spinner');
    const buttonText = document.getElementById('button-text');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        setLoading(true);

        const baseUrl = window.location.origin;
        const returnUrl = `${baseUrl}/orders/confirmation/${orderNumber}/`;

        const { error } = await stripe.confirmPayment({
            elements,
            confirmParams: {
                return_url: returnUrl,
            },
            redirect: 'always'
        });

        if (error) {
            let errorMessage = "An unexpected error occurred.";
             if (error.type === "card_error" || error.type === "validation_error") {
                errorMessage = error.message;
            }
            console.error("Stripe Error:", error.message);
            alert(`Payment Error: ${errorMessage}`);

            setLoading(false);
        }
    });

    function setLoading(isLoading) {
        if (isLoading) {
            submitButton.disabled = true;
            spinner.classList.remove('d-none');
            buttonText.classList.add('d-none');
        } else {
            submitButton.disabled = false;
            spinner.classList.add('d-none');
            buttonText.classList.remove('d-none');
        }
    }

    paymentElement.on('change', function(event) {
        if (event.error) {
            console.warn("Payment Element Error:", event.error.message);
        } else {
            // Clear error feedback
        }
    });
});