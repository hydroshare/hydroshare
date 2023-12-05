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
            if (query === "" || this.selectedAgency !== null){
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
            this.selectedAgency = null

            if (this.newAgency.trim() === "") {
                return; // Empty string detected
            }else if (this.newAgency.length > 250) {
                this.error = "Your funder is too long. Ensure it has at most 100 characters.";
                return;
            }

            this.error = "";
            if ($.inArray(this.newAgency, this.fundingAgencyNames) >= 0) {
                this.showIsDuplicate = true;
                this.error = "Duplicate";
            }
            else {
                this.fundingAgencies.push(this.newAgency);
            }
            if(this.selectedAgency){
                this.updateUri()
            }
        },
        updateUri: function() {
            this.recommendedUrl = this.selectedAgency.uri
        }
    },
    watch: {
        newAgency: debounce(function(funder) { 
            this.getCrossrefFunders(funder) }, 500),
        selectedAgency: function(newer, old){ 
            if (newer !== null)
            this.updateUri() 
        }
      }
});