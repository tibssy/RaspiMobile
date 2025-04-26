const mailchimpMessageDelay = 3000;

function displayAjaxMessage(message, level) {
    const $ = window.jQuery || window.mcj$;
    if (!$) {
        console.error("jQuery not available for displayAjaxMessage");
        return;
    }

    const messageContainer = $('#messages');
    if (!messageContainer.length) {
        console.error("Messages container #messages not found.");
        return;
    }

    messageContainer.find('.mc-ajax-message').remove();

    let alertClass = 'primary';
    if (level === 'success') { alertClass = 'success'; }
    else if (level === 'error') { alertClass = 'danger'; }
    else if (level === 'info') { alertClass = 'info'; }
    else if (level === 'warning') { alertClass = 'warning'; }

    const alertHtml = `
        <div class="alert alert-${alertClass} alert-dismissible fade show mc-ajax-message" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;

    messageContainer.append(alertHtml);

    const newAlertElement = messageContainer.find('.mc-ajax-message:last-child')[0];

    if (newAlertElement) {
        const bsAlertInstance = bootstrap.Alert.getOrCreateInstance(newAlertElement);
        const timeoutId = setTimeout(() => {
            if (bsAlertInstance) {
                bsAlertInstance.close();
            } else {
                newAlertElement.remove();
            }
        }, mailchimpMessageDelay);
    }
}

(function($) {
    if (!$) {
      console.error("jQuery or $mcj not available for Mailchimp AJAX script.");
      return;
    }

    $(document).ready(function() {
        const form = $('#mc-embedded-subscribe-form');
        if (!form.length) return;

        form.submit(function(event) {
            event.preventDefault();

            $('#mce-error-response').hide();
            $('#mce-success-response').hide();

            if ($('#mce-EMAIL').val().trim() === '') {
                displayAjaxMessage('Please enter your email address.', 'error');
                return;
            }

            const $submitButton = $('#mc-embedded-subscribe');
            const originalButtonHtml = $submitButton.html();
            $submitButton.prop('disabled', true).html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Subscribing...');
            let mailchimpUrl = form.attr('action');
            mailchimpUrl = mailchimpUrl.replace('/post?', '/post-json?').concat('&c=?');

            $.ajax({
                url: mailchimpUrl,
                data: form.serialize(),
                dataType: 'jsonp',
                contentType: "application/json; charset=utf-8",
                success: function(data) {
                    $submitButton.prop('disabled', false).html(originalButtonHtml);

                    if (data.result === "success") {
                        displayAjaxMessage(data.msg, 'success');
                        form[0].reset();
                    } else {
                        let errorMessage = data.msg || 'An unknown error occurred.';

                        if (errorMessage.includes("is already subscribed")) {
                             errorMessage = 'You are already subscribed. Thank you!';
                         } else if (errorMessage.includes("invalid email") || errorMessage.includes("Please enter a value") || errorMessage.includes("valid email")) {
                             errorMessage = 'Please enter a valid email address.';
                         }

                        displayAjaxMessage(errorMessage, 'error');
                    }
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    $submitButton.prop('disabled', false).html(originalButtonHtml);
                    console.error("Mailchimp AJAX error:", textStatus, errorThrown);
                    displayAjaxMessage('An error occurred while trying to subscribe. Please try again later.', 'error');
                }
            });
        });
    });
}(window.jQuery || window.mcj$));