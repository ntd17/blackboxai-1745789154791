document.addEventListener('DOMContentLoaded', function() {
    // Initialize all Materialize components
    initializeMaterialize();
    
    // Set up AJAX request handling
    setupAjaxHandling();
    
    // Initialize dynamic content handlers
    initializeDynamicContent();
    
    // Set up form validation
    setupFormValidation();
});

// Initialize Materialize components
function initializeMaterialize() {
    // Sidenav
    const sidenavElems = document.querySelectorAll('.sidenav');
    M.Sidenav.init(sidenavElems);

    // Dropdowns
    const dropdownElems = document.querySelectorAll('.dropdown-trigger');
    M.Dropdown.init(dropdownElems, {
        coverTrigger: false,
        constrainWidth: false
    });

    // Floating Action Button
    const fabElems = document.querySelectorAll('.fixed-action-btn');
    M.FloatingActionButton.init(fabElems);

    // Modals
    const modalElems = document.querySelectorAll('.modal');
    M.Modal.init(modalElems);

    // Select inputs
    const selectElems = document.querySelectorAll('select');
    M.FormSelect.init(selectElems);

    // Date pickers
    const dateElems = document.querySelectorAll('.datepicker');
    M.Datepicker.init(dateElems, {
        format: 'yyyy-mm-dd',
        i18n: getDatepickerTranslations()
    });

    // Tooltips
    const tooltipElems = document.querySelectorAll('.tooltipped');
    M.Tooltip.init(tooltipElems);
}

// Set up AJAX request handling
function setupAjaxHandling() {
    // Add CSRF token to all AJAX requests
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
    if (csrfToken) {
        $.ajaxSetup({
            beforeSend: function(xhr, settings) {
                if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrfToken);
                }
            }
        });
    }

    // Global AJAX error handling
    $(document).ajaxError(function(event, jqXHR, settings, error) {
        console.error('AJAX Error:', error);
        M.toast({
            html: t('site.error'),
            classes: 'red'
        });
    });
}

// Initialize dynamic content handlers
function initializeDynamicContent() {
    // Handle dynamic content loading
    $(document).on('click', '[data-load]', function(e) {
        e.preventDefault();
        const url = $(this).data('load');
        const target = $(this).data('target');
        
        $(target).html(t('site.loading'));
        
        $.get(url)
            .done(function(response) {
                $(target).html(response);
                translateElement($(target)[0]);
                initializeMaterialize();
            })
            .fail(function() {
                $(target).html(t('site.error'));
            });
    });

    // Handle dynamic form submission
    $(document).on('submit', 'form[data-remote]', function(e) {
        e.preventDefault();
        const form = $(this);
        const url = form.attr('action');
        const method = form.attr('method') || 'POST';
        
        $.ajax({
            url: url,
            method: method,
            data: new FormData(form[0]),
            processData: false,
            contentType: false
        })
        .done(function(response) {
            if (response.redirect) {
                window.location.href = response.redirect;
            } else if (response.message) {
                M.toast({html: response.message});
            }
        })
        .fail(function(jqXHR) {
            const message = jqXHR.responseJSON?.error || t('site.error');
            M.toast({html: message, classes: 'red'});
        });
    });
}

// Set up form validation
function setupFormValidation() {
    $(document).on('submit', 'form[data-validate]', function(e) {
        const form = $(this)[0];
        if (form.checkValidity() === false) {
            e.preventDefault();
            e.stopPropagation();
            
            // Show validation messages
            Array.from(form.elements).forEach(input => {
                if (!input.validity.valid) {
                    const errorMessage = input.dataset.errorMsg || getDefaultErrorMessage(input);
                    M.toast({html: errorMessage, classes: 'red'});
                }
            });
        }
        form.classList.add('was-validated');
    });
}

// Get default error message based on validation type
function getDefaultErrorMessage(input) {
    if (input.validity.valueMissing) {
        return t('validation.required');
    }
    if (input.validity.typeMismatch) {
        return t('validation.invalid_type');
    }
    if (input.validity.patternMismatch) {
        return t('validation.pattern');
    }
    if (input.validity.tooShort) {
        return t('validation.too_short');
    }
    if (input.validity.tooLong) {
        return t('validation.too_long');
    }
    return t('validation.invalid');
}

// Get datepicker translations based on current language
function getDatepickerTranslations() {
    const translations = {
        'en': {
            months: ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
            monthsShort: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            weekdays: ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
            weekdaysShort: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
            weekdaysAbbrev: ['S', 'M', 'T', 'W', 'T', 'F', 'S']
        },
        'pt': {
            months: ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'],
            monthsShort: ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'],
            weekdays: ['Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado'],
            weekdaysShort: ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'],
            weekdaysAbbrev: ['D', 'S', 'T', 'Q', 'Q', 'S', 'S']
        },
        'es': {
            months: ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'],
            monthsShort: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'],
            weekdays: ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'],
            weekdaysShort: ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'],
            weekdaysAbbrev: ['D', 'L', 'M', 'M', 'J', 'V', 'S']
        }
    };
    
    return translations[window.i18n.currentLang] || translations['en'];
}
