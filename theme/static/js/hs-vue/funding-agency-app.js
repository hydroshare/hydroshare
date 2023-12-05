let debounce = function(func, wait, immediate) {
    let timeout, result;
    return function() {
      let context = this, args = arguments;
      let later = function() {
        timeout = null;
        if (!immediate) result = func.apply(context, args);
      };
      let callNow = immediate && !timeout;
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
      if (callNow) result = func.apply(context, args);
      return result;
    };
}

let fundingAgenciesApp = new Vue({
    el: '#add-funding-agency',
    delimiters: ['${', '}'],
    components: {
        VueBootstrapTypeahead
    },
    data: {
        newAgency: '',
        fundingAgencies: RES_FUNDING_AGENCIES,
        fundingAgencyNames: [],
        fundingAgencyUrls: [],
        recommendedUrl: "",
        selectedAgency: null,
        crossrefFunders: [],
        CROSSREF_API_URL: 'https://api.crossref.org/funders?query=:query',
        MIN_SEARCH_LEN: 3,
        DEBOUNCE_API_MS: 500,
        timeout: null,
        showIsDuplicate: false,
        error: '',
        isPending: false
    },
    mounted(){
        this.fundingAgencyNames = this.fundingAgencies.map(a => a.agency_name);
        this.fundingAgencyUrls = this.fundingAgencies.map(a => a.identifier);
    },
    methods: {
        getCrossrefFunders: async function(query) {
            if (query === "" || this.showIsDuplicate){
                return
            }
            this.isPending = true
            query = `${query}&mailto=help@cuahsi.org`
            const res = await fetch(this.CROSSREF_API_URL.replace(':query', query))
            const result = await res.json()
            this.crossrefFunders = result.message.items
            this.isPending = false
        },
        checkAgency: function () {
            this.showIsDuplicate = false;  // Reset

            if (this.newAgency.trim() === "") {
                return false; // Empty string detected
            }else if (this.newAgency.length > 250) {
                this.error = "Your funder is too long. Ensure it has at most 100 characters.";
                return false;
            }

            this.error = "";
            if ($.inArray(this.newAgency, this.fundingAgencyNames) >= 0) {
                this.showIsDuplicate = true;
                this.error = "Duplicate";
                return false
            }
            if(this.selectedAgency){
                this.updateUri()
            }
            return true
        },
        updateUri: function() {
            this.recommendedUrl = this.selectedAgency.uri
        },
        formSubmit: function(){
            alert("sub")
        },
        selectAgency: function(event) {
            this.isPending=false
            this.selectedAgency = event;
        }
    },
    watch: {
        newAgency: function(funder){
            if(!this.checkAgency() || funder.length < this.MIN_SEARCH_LEN){
                return
            }
            if (this.timeout) clearTimeout(this.timeout); 
            this.timeout = setTimeout(() => {
                this.getCrossrefFunders(funder);
            }, this.DEBOUNCE_API_MS);
        },
        selectedAgency: function(newer, _){ 
            // TODO: pending is shown after select
            // 
            this.isPending = false
            if (newer !== null){
                this.updateUri()
                this.fundingAgencies.push(this.newAgency);
            }
        }
      },
      computed: {
        allowSubmit: function () {
            if (this.newAgency.trim() === "") return false
            if (this.error || this.showIsDuplicate) return false
            return true
        }
      }
});