/**
 * @file payments.js
 * @description Handles the Stripe Payment Element integration on the payment page.
 * Initializes Stripe.js, creates and mounts the Payment Element with custom appearance,
 * and handles the payment form submission to confirm the payment with Stripe.
 * It also manages the loading state of the submit button during payment processing.
 */

document.addEventListener("DOMContentLoaded", function () {
    const stripePublicKey = JSON.parse(
        document.getElementById("id_stripe_public_key").textContent
    );
    const clientSecret = JSON.parse(
        document.getElementById("id_client_secret").textContent
    );
    const orderNumberElement = document.getElementById("order-number");
    const orderNumber = orderNumberElement
        ? orderNumberElement.dataset.orderNumber
        : null;
    const stripe = Stripe(stripePublicKey);

    const primaryBackgroundVar = "#45c95d";
    const secondaryColorVar = "#198754";
    const dangerColorVar = "#dc3545";
    const boxShadowNormalVar = "0 2px 4px #00000080";

    /**
     * Appearance object for customizing the Stripe Payment Element.
     * @see https://stripe.com/docs/elements/appearance-api
     * @type {object}
     */
    const appearance = {
        theme: "flat",
        variables: {
            colorPrimary: secondaryColorVar,
            colorBackground: "#fff",
            focusBoxShadow: boxShadowNormalVar,
        },
        rules: {
            ".Input": {
                border: "1px solid transparent",
                borderBottom: `1px solid ${primaryBackgroundVar}`,
                borderRadius: "0px",
                padding: "0.6rem 0.75rem",
                transition:
                    "transform 0.3s ease-in-out, background-color 0.3s ease-in-out, border 0.3s ease-in-out, box-shadow 0.3s ease-in-out, border-radius 0.3s ease-in-out",
                outline: "none",
            },
            ".Input:focus": {
                border: `1px solid ${primaryBackgroundVar}`,
                borderRadius: "6px",
            },
            ".Input--invalid": {
                border: "1px solid transparent",
                borderBottom: `1px solid ${dangerColorVar}`,
                borderRadius: "0px",
                padding: "0.6rem 0.75rem",
                outline: "none",
                boxShadow: "none",
            },
            ".Input--invalid:focus": {
                border: `1px solid ${dangerColorVar}`,
                borderRadius: "6px",
            },
            ".Label": {
                fontWeight: "500",
                paddingLeft: "0.5rem",
                paddingBottom: "0.5rem",
            },
            ".Tab": {
                borderRadius: "6px",
                border: "1px solid transparent",
            },
            ".Tab:hover": {
                boxShadow: boxShadowNormalVar,
                border: `1px solid ${primaryBackgroundVar}`,
            },
            ".Tab--selected": {
                border: "1px solid transparent",
                backgroundColor: secondaryColorVar,
                color: "#fff",
            },
        },
    };

    /**
     * Stripe Elements instance created with the defined appearance and clientSecret.
     * Used to create individual Element instances (like the Payment Element).
     * @type {StripeElements}
     */
    const elements = stripe.elements({ appearance, clientSecret });

    const paymentElementOptions = {
        layout: "tabs",
    };

    const paymentElement = elements.create("payment", paymentElementOptions);
    paymentElement.mount("#payment-element");

    const form = document.getElementById("payment-form");
    const submitButton = document.getElementById("submit-button");
    const spinner = document.getElementById("spinner");
    const buttonText = document.getElementById("button-text");

    // Add submit event listener to the payment form
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        setLoading(true);

        const baseUrl = window.location.origin;
        const returnUrl = `${baseUrl}/orders/confirmation/${orderNumber}/`;

        const { error } = await stripe.confirmPayment({
            elements,
            confirmParams: {
                return_url: returnUrl,
            },
            redirect: "always",
        });

        if (error) {
            let errorMessage = "An unexpected error occurred.";
            if (
                error.type === "card_error" ||
                error.type === "validation_error"
            ) {
                errorMessage = error.message;
            }
            console.error("Stripe Error:", error.message);
            alert(`Payment Error: ${errorMessage}`);

            setLoading(false);
        }
    });

    /**
     * Toggles the loading state of the submit button.
     * Disables the button and shows a spinner while loading.
     * @param {boolean} isLoading - True to show loading state, false to reset.
     */
    function setLoading(isLoading) {
        if (isLoading) {
            submitButton.disabled = true;
            spinner.classList.remove("d-none");
            buttonText.classList.add("d-none");
        } else {
            submitButton.disabled = false;
            spinner.classList.add("d-none");
            buttonText.classList.remove("d-none");
        }
    }

    paymentElement.on("change", function (event) {
        if (event.error)
            console.warn("Payment Element Error:", event.error.message);
    });
});
