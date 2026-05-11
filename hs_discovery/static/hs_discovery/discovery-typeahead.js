(function () {
  var app = window.HSDiscovery = window.HSDiscovery || {};

  function registerTypeaheadComponent() {
    if (!window.Alpine) {
      return;
    }

    window.Alpine.data('discoveryTypeahead', function () {
      return {
        query: '',
        suggestions: [],
        activeIndex: -1,
        isOpen: false,
        requestSerial: 0,

        init: function () {
          var input = this.$refs.input;
          this.query = input ? (input.value || '') : '';
        },

        closeMenu: function () {
          this.isOpen = false;
          this.activeIndex = -1;
          this.suggestions = [];
        },

        maybeFetchSuggestions: function () {
          if (this.query.trim().length >= 3 && !this.suggestions.length) {
            this.fetchSuggestions();
          }
        },

        moveDown: function () {
          if (!this.suggestions.length) {
            return;
          }
          this.isOpen = true;
          this.activeIndex = (this.activeIndex + 1) % this.suggestions.length;
        },

        moveUp: function () {
          if (!this.suggestions.length) {
            return;
          }
          this.isOpen = true;
          this.activeIndex = this.activeIndex <= 0 ? this.suggestions.length - 1 : this.activeIndex - 1;
        },

        handleEnter: function (event) {
          if (this.isOpen && this.activeIndex >= 0) {
            event.preventDefault();
            this.selectSuggestion(this.suggestions[this.activeIndex]);
          }
        },

        handleBlur: function () {
          var self = this;
          setTimeout(function () {
            self.closeMenu();
          }, 120);
        },

        selectSuggestion: function (value) {
          var input = this.$refs.input;
          this.query = value;
          if (input) {
            input.value = value;
          }
          this.closeMenu();
          if (window.htmx && input) {
            var eventName = input.dataset.applyOnSelect === 'true' ? 'typeahead-select' : 'change';
            this.$nextTick(function () {
              window.htmx.trigger(input, eventName);
            });
          }
        },

        clearTerm: function () {
          var input = this.$refs.input;
          this.query = '';
          if (input) {
            input.value = '';
          }
          this.closeMenu();
          if (window.htmx && input) {
            this.$nextTick(function () {
              window.htmx.trigger(input, 'term-cleared');
            });
          }
        },

        extractSuggestions: function (payload, query) {
          var lowerQuery = (query || '').toLowerCase();
          var values = [];
          (payload || []).forEach(function (entry) {
            (entry.highlights || []).forEach(function (highlight) {
              (highlight.texts || []).forEach(function (text) {
                if (text.type === 'hit' && text.value) {
                  var candidate = String(text.value).trim();
                  if (candidate && candidate.toLowerCase().indexOf(lowerQuery) !== -1) {
                    values.push(candidate);
                  }
                }
              });
            });
          });
          return Array.from(new Set(values)).slice(0, 8);
        },

        fetchSuggestions: async function () {
          var input = this.$refs.input;
          var query = this.query.trim();
          var typeaheadUrl = input ? (input.dataset.typeaheadUrl || '') : '';
          var field = input ? (input.dataset.typeaheadField || 'term') : 'term';

          if (query.length < 3 || !typeaheadUrl) {
            this.closeMenu();
            return;
          }

          var requestId = ++this.requestSerial;

          try {
            var response = await fetch(
              typeaheadUrl + '?term=' + encodeURIComponent(query) + '&field=' + encodeURIComponent(field),
              { credentials: 'same-origin' }
            );

            if (!response.ok || requestId !== this.requestSerial || this.query.trim() !== query) {
              if (requestId === this.requestSerial && !response.ok) {
                this.closeMenu();
              }
              return;
            }

            var payload = await response.json();
            if (requestId !== this.requestSerial || this.query.trim() !== query) {
              return;
            }

            this.suggestions = this.extractSuggestions(payload, query);
            this.activeIndex = -1;
            this.isOpen = this.suggestions.length > 0;
          } catch (_error) {
            if (requestId === this.requestSerial) {
              this.closeMenu();
            }
          }
        }
      };
    });
  }

  document.addEventListener('alpine:init', registerTypeaheadComponent);

  app.initializeTypeaheads = function () {};
})();
