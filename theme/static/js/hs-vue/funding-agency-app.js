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
    el: '#funding-agency-app',
    delimiters: ['${', '}'],
    components: {
        VueBootstrapTypeahead
    },
    data: {
        agencyName: '',
        fundingAgencies: RES_FUNDING_AGENCIES,
        resourceId: SHORT_ID,
        fundingAgencyNames: [],
        fundingAgencyUrls: [],
        selectedAgency: null,
        crossrefFunders: [],
        CROSSREF_API_URL: 'https://api.crossref.org/funders?query=:query',
        MIN_SEARCH_LEN: 3,
        DEBOUNCE_API_MS: 500,
        timeout: null,
        showIsDuplicate: false,
        error: '',
        isPending: false,
        mode: null, //add or edit
        currentlyEditing: {},
        deleteUrl: "",
        currentlyDeleting: {}
    },
    mounted(){
        this.fundingAgencyNames = this.fundingAgencies.map(a => a.agency_name);
        this.fundingAgencyUrls = this.fundingAgencies.map(a => a.agency_url);
    },
    methods: {
        getCrossrefFunders: async function(query) {
            if (query === "" || this.showIsDuplicate){
                return
            }
            this.isPending = true
            // https://api.crossref.org/swagger-ui/index.html#/Funders/get_funders
            query = query.replace(" ", "+")
            query = `${query}&mailto=help@cuahsi.org`
            const res = await fetch(this.CROSSREF_API_URL.replace(':query', query))
            const result = await res.json()
            this.crossrefFunders = result.message.items
            this.isPending = false
        },
        checkAgency: function () {
            this.showIsDuplicate = false;  // Reset

            if (this.agencyName.trim() === "") {
                return false; // Empty string detected
            }else if (this.agencyName.length > 250) {
                this.error = "Your funder is too long. Ensure it has at most 100 characters.";
                return false;
            }

            this.error = "";
            if ($.inArray(this.agencyName, this.fundingAgencyNames) >= 0) {
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
            this.currentlyEditing.agency_url = this.selectedAgency.uri
        },
        formSubmit: function(){
            alert("sub")
        },
        selectAgency: function(event) {
            this.isPending=false
            this.selectedAgency = event;
            this.checkAgency();
        },
        clearSelectedAgency: function(){
            this.selectedAgency = null;
        },
        openEditModal(id){
            this.mode = 'Edit';
            this.currentlyEditing = this.fundingAgencies.filter((agency)=>{
                return agency.agency_id == id;
            })[0]
            this.agencyName = this.currentlyEditing.agency_name;
            // TODO: edit doesnt populate name!
        },
        openDeleteModal(id){
            this.currentlyDeleting = this.fundingAgencies.filter((agency)=>{
                return agency.agency_id == id;
            })[0]
            this.deleteUrl = `/hsapi/_internal/${ this.resourceId }/fundingagency/${ id }/delete-metadata/`
        }
    },
    watch: {
        agencyName: function(funder){
            if(funder.length < this.MIN_SEARCH_LEN || this.selectedAgency){
                return
            }
            this.checkAgency()
            if (this.timeout) clearTimeout(this.timeout); 
            this.timeout = setTimeout(() => {
                this.getCrossrefFunders(funder);
            }, this.DEBOUNCE_API_MS);
        },
        selectedAgency: function(newer, _){ 
            this.isPending = false
            if (newer !== null){
                this.updateUri()
                this.fundingAgencies.push(this.agencyName);
            }
        }
      },
      computed: {
        allowSubmit: function () {
            if (this.agencyName.trim() === "") return false
            if (this.error || this.showIsDuplicate) return false
            return true
        },
        actionUri: function() {
            if (this.mode === 'Edit'){
                return `/hsapi/_internal/${ this.resourceId }/fundingagency/${ this.currentlyEditing.agency_id }/update-metadata/`
            }else{
                return `/hsapi/_internal/${ this.resourceId }/fundingagency/add-metadata/`
            }
        }
      }
});