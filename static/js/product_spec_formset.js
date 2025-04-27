/**
 * @file product_spec_formset.js
 * @description Handles the client-side addition of new specification forms
 * to a Django inline formset, specifically for product specifications.
 * It clones a template form, updates its IDs and names based on the formset's
 * management form data, appends it to the container, and increments the total
 * forms count.
 */

document.addEventListener("DOMContentLoaded", function () {
    const addSpecButton = document.getElementById("add-spec-button");
    const formsetContainer = document.getElementById(
        "specifications-formset-container"
    );
    const totalFormsInput = document.querySelector(
        'input[name="specs-TOTAL_FORMS"]'
    );
    const emptyFormTemplate = document.getElementById(
        "empty-spec-form-template"
    );

    /**
     * Event listener callback for the 'click' event on the 'Add Specification' button.
     * Clones the empty form template, updates the form index placeholders ('__prefix__')
     * in attributes like 'id', 'name', and 'for', appends the new form row to the DOM,
     * increments the TOTAL_FORMS count, and focuses the first input in the new row.
     */
    addSpecButton.addEventListener("click", function () {
        const newFormFragment = emptyFormTemplate.content.cloneNode(true);
        const newFormRow = newFormFragment.firstElementChild;
        const currentFormCount = parseInt(totalFormsInput.value);

        newFormRow
            .querySelectorAll("input, select, textarea, label")
            .forEach((element) => {
                ["id", "name", "for"].forEach((attribute) => {
                    const value = element.getAttribute(attribute);
                    if (value) {
                        element.setAttribute(
                            attribute,
                            value.replace("__prefix__", currentFormCount)
                        );
                    }
                });
            });

        // Add the newly processed form row to the container
        formsetContainer.appendChild(newFormRow);

        // Increment the value of the TOTAL_FORMS management input
        totalFormsInput.value = currentFormCount + 1;

        // Find the first visible input or select element in the new row to focus it
        const firstInput = newFormRow.querySelector(
            "select, input:not([type=hidden])"
        );

        if (firstInput) {
            firstInput.focus();
        }
    });
});
