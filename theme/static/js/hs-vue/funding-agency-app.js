let fundingAgenciesApp = new Vue({
    el: '#funding-agency-app',
    delimiters: ['${', '}'],
    components: {
        VueBootstrapTypeahead
    },
    data: {
        agencyName: '',
        fundingAgencies: RES_FUNDING_AGENCIES, // funding agencies from the backend/Django
        resourceId: SHORT_ID,
        fundingAgencyNames: [],
        selectedAgency: null, // keep track of the selected agency from the dropdown
        crossrefFunders: [], // array of funders to be filled from crossref api
        CROSSREF_API_URL: 'https://api.crossref.org/funders?query=:query',
        MIN_SEARCH_LEN: 3, // min # of chars before running a query
        DEBOUNCE_API_MS: 500, // debounce api requests
        timeout: null, // used for debouncing
        notification: {},
        isPending: false, // is api fetch pending
        mode: null, // mode for the modals -- Add or Edit
        currentlyEditing: {}, // store the funder that we are editing
        deleteUrl: "", // Django endpoint to call for deleting a funder
        currentlyDeleting: {} // store the funder that we are deleting
    },
    mounted(){
        this.fundingAgencyNames = this.fundingAgencies.map(a => a.agency_name);
    },
    methods: {
        getCrossrefFunders: async function(query) {
            if (query === "" || this.notification.error){
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
            this.notification = {};

            if (this.agencyName.trim() === "") {
                return false; // Empty string detected
            }else if (this.agencyName.length > 250) {
                this.notification = { error: "Your funder is too long. Ensure it has at most 250 characters." }
                return false;
            }

            if (this.mode == "Add" && $.inArray(this.agencyName, this.fundingAgencyNames) >= 0) {
                this.notification = { error: "You already added this funder for this resource" };
                return false
            }

            if(this.selectedAgency){
                this.updateUri()
            }else{
                this.notification = { info: "We recommend that you select from the list of known funding agencies."}
                return false
            }
            return true
        },
        updateUri: function() {
            // Auto-populated the URL input field when we select an agency from the dropdown
            this.currentlyEditing.agency_url = this.selectedAgency.uri
        },
        selectAgency: function(event) {
            this.isPending=false
            this.selectedAgency = event;
            this.checkAgency();
        },
        clearSelectedAgency: function(){
            this.selectedAgency = null;
        },
        openAddModal(){
            this.mode = 'Add';
            this.currentlyEditing = {}
            this.agencyName = ""
            // open source bug https://github.com/alexurquhart/vue-bootstrap-typeahead/issues/19
            this.$refs.agencyName.inputValue = "";
        },
        openEditModal(id){
            this.mode = 'Edit';
            this.currentlyEditing = this.fundingAgencies.filter((agency)=>{
                return agency.agency_id == id;
            })[0]
            this.agencyName = this.currentlyEditing.agency_name;
            // open source bug https://github.com/alexurquhart/vue-bootstrap-typeahead/issues/19
            this.$refs.agencyName.inputValue = this.currentlyEditing.agency_name;
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
                this.notification = {}
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
                // this.fundingAgencies.push(this.agencyName);
            }
        }
      },
      computed: {
        allowSubmit: function () {
            if ( this.agencyName.trim() === "" ) return false
            if ( this.notification.error ) return false
            return true
        },
        actionUri: function() {
            // Get the appropriate form action endpoint for either editing or adding funding agencies
            if (this.mode === 'Edit'){
                return `/hsapi/_internal/${ this.resourceId }/fundingagency/${ this.currentlyEditing.agency_id }/update-metadata/`
            }else{
                return `/hsapi/_internal/${ this.resourceId }/fundingagency/add-metadata/`
            }
        }
      }
});