document.addEventListener('DOMContentLoaded', function() {
    const addSpecButton = document.getElementById('add-spec-button');
    const formsetContainer = document.getElementById('specifications-formset-container');
    const totalFormsInput = document.querySelector('input[name="specs-TOTAL_FORMS"]');
    const emptyFormTemplate = document.getElementById('empty-spec-form-template');

    addSpecButton.addEventListener('click', function() {
        const newFormFragment = emptyFormTemplate.content.cloneNode(true);
        const newFormRow = newFormFragment.firstElementChild;
        const currentFormCount = parseInt(totalFormsInput.value);

        newFormRow.querySelectorAll('input, select, textarea, label').forEach(element => {
            ['id', 'name', 'for'].forEach(attribute => {
                const value = element.getAttribute(attribute);
                if (value) {
                    element.setAttribute(attribute, value.replace('__prefix__', currentFormCount));
                }
            });
        });

        formsetContainer.appendChild(newFormRow);
        totalFormsInput.value = currentFormCount + 1;
        const firstInput = newFormRow.querySelector('select, input:not([type=hidden])');

        if (firstInput) {
            firstInput.focus();
        }
    });
});