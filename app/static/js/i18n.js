class I18nManager {
    constructor() {
        this.currentLang = localStorage.getItem('preferredLanguage') || 'en';
        this.translations = window.translations || {};
        this.observers = [];
    }

    // Initialize language handling
    init() {
        this.setLanguage(this.currentLang, false);
        this.setupLanguageSelector();
        this.translatePage();
    }

    // Set up language selector buttons
    setupLanguageSelector() {
        document.querySelectorAll('.lang-select').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const lang = e.currentTarget.dataset.lang;
                this.setLanguage(lang);
            });

            // Highlight current language
            if (btn.dataset.lang === this.currentLang) {
                btn.classList.add('active');
            }
        });
    }

    // Set language and update UI
    setLanguage(lang, translate = true) {
        if (this.translations[lang]) {
            this.currentLang = lang;
            localStorage.setItem('preferredLanguage', lang);
            
            // Update UI indicators
            document.documentElement.lang = lang;
            document.querySelectorAll('.lang-select').forEach(btn => {
                btn.classList.toggle('active', btn.dataset.lang === lang);
            });

            // Update page content
            if (translate) {
                this.translatePage();
            }

            // Notify observers
            this.notifyObservers();
        }
    }

    // Translate the entire page
    translatePage() {
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.dataset.i18n;
            const translation = this.translate(key);
            
            if (translation) {
                // Handle input placeholders
                if (element.tagName === 'INPUT' && element.hasAttribute('placeholder')) {
                    element.placeholder = translation;
                } else {
                    element.textContent = translation;
                }
            }
        });

        // Handle dynamic content
        this.notifyObservers();
    }

    // Get translation for a key
    translate(key) {
        return key.split('.').reduce((obj, i) => obj ? obj[i] : null, this.translations[this.currentLang]);
    }

    // Format date according to current language
    formatDate(date) {
        return new Date(date).toLocaleDateString(this.currentLang);
    }

    // Format number according to current language
    formatNumber(number) {
        return new Number(number).toLocaleString(this.currentLang);
    }

    // Format currency according to current language
    formatCurrency(amount) {
        return new Intl.NumberFormat(this.currentLang, {
            style: 'currency',
            currency: this.getCurrencyForLanguage()
        }).format(amount);
    }

    // Get appropriate currency code for current language
    getCurrencyForLanguage() {
        const currencyMap = {
            'en': 'USD',
            'pt': 'BRL',
            'es': 'COP'
        };
        return currencyMap[this.currentLang] || 'USD';
    }

    // Add observer for dynamic content
    addObserver(callback) {
        this.observers.push(callback);
    }

    // Notify all observers of language change
    notifyObservers() {
        this.observers.forEach(callback => callback(this.currentLang));
    }

    // Helper method to translate dynamic content
    translateDynamic(element) {
        element.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.dataset.i18n;
            const translation = this.translate(key);
            if (translation) {
                if (el.tagName === 'INPUT' && el.hasAttribute('placeholder')) {
                    el.placeholder = translation;
                } else {
                    el.textContent = translation;
                }
            }
        });
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    window.i18n = new I18nManager();
    window.i18n.init();
});

// Helper function to translate dynamic content
function translateElement(element) {
    window.i18n.translateDynamic(element);
}

// Helper function to get translation
function t(key) {
    return window.i18n.translate(key);
}

// Helper function to format date
function formatDate(date) {
    return window.i18n.formatDate(date);
}

// Helper function to format number
function formatNumber(number) {
    return window.i18n.formatNumber(number);
}

// Helper function to format currency
function formatCurrency(amount) {
    return window.i18n.formatCurrency(amount);
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        I18nManager,
        t,
        formatDate,
        formatNumber,
        formatCurrency
    };
}
