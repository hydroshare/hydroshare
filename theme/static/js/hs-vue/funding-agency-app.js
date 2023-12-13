let fundingAgenciesApp = new Vue({
  el: "#funding-agency-app",
  delimiters: ["${", "}"],
  components: {
    VueBootstrapTypeahead,
  },
  data: {
    agencyName: "",
    fundingAgencies: RES_FUNDING_AGENCIES, // funding agencies from the backend/Django
    unmatchedFunders: [], // funders not found in Crossref
    resourceId: SHORT_ID,
    resourceMode: RESOURCE_MODE, // edit/view
    crossrefFunders: [], // array of funders to be filled from crossref api
    crossrefFundersNames: [],
    crossrefSelected: false,
    CROSSREF_API_URL: "https://api.crossref.org/funders?query=:query",
    MIN_SEARCH_LEN: 3, // min # of chars before running a query
    DEBOUNCE_API_MS: 500, // debounce api requests
    timeout: null, // used for debouncing
    notifications: [],
    isPending: false, // is api fetch pending
    mode: null, // mode for the modals -- Add or Edit
    currentlyEditing: {}, // store the funder that we are editing
    deleteUrl: "", // Django endpoint to call for deleting a funder
    currentlyDeleting: {}, // store the funder that we are deleting
  },
  mounted() {
    if (this.resourceMode === "Edit") {
      this.checkFunderNamesExistInCrossref(this.fundingAgencies);
    }
  },
  methods: {
    checkFunderNamesExistInCrossref: async function (funders) {
      for (let funder of funders) {
        const match = await this.funderNameExistsInCrossref(funder.agency_name);
        if (!match) {
          this.unmatchedFunders.push(funder.agency_name);
        }
      }
    },
    funderNameExistsInCrossref: async function (funderName) {
      try {
        const lowerFunderName = funderName.toLowerCase();
        const funders = await this.queryCrossrefFunderList(funderName);
        if (funders == null) return false
        for (let funder of funders) {
          if (funder.name.toLowerCase() == lowerFunderName) return true;
          for (let alt in funder["alt-names"]) {
            if (alt == lowerFunderName) return true;
          }
        }
        return false;
      } catch (e) {
        console.error(`Error checking funding name in Crossref: ${e}`);
        return true; // default to success to avoid false positive messages if crossreff api is unresponsive
      }
    },
    queryCrossrefFunderList: async function (funderName) {
      try {
        let words = funderName.split(" ");
        words = words.map((w) => encodeURIComponent(w));
        let query = words.join("+");
        query = `${query}&mailto=help@cuahsi.org`;
        // https://api.crossref.org/swagger-ui/index.html#/Funders/get_funders
        const res = await fetch(this.CROSSREF_API_URL.replace(":query", query));
        const result = await res.json();
        const funders = result.message.items;
        return funders;
      } catch (e) {
        console.error(`Error querying Crossref API: ${e}`);
      }
      return null;
    },
    getCrossrefFunders: async function (funderName) {
      if (funderName === "" || this.notifications.error) {
        return;
      }
      this.isPending = true;
      this.crossrefFunders = await this.queryCrossrefFunderList(funderName)
      if (this.crossrefFunders !== null){
        this.crossrefFundersNames = this.crossrefFundersNames.concat(
          this.crossrefFunders.map((f) => f.name)
        );
      }
      this.isPending = false;
    },
    checkAgency: function () {
      this.notifications = [];

      if (this.agencyName.trim() !== this.agencyName) {
        this.notifications.push({
          error: "Agency name has leading or trailing whitespace.",
        });
      }

      if (this.agencyName.length > 250) {
        this.notifications.push({
          error:
            "Agency name is too long. Ensure it has at most 250 characters.",
        });
      }

      if (this.isDuplicateFunder(this.currentlyEditing)) {
        // TODO: in edit mode, this message can be confusing
        this.notifications.push({
          error: "A funding agency matching these values already exists",
        });
      }

      if (!this.isNameFromCrossref(this.agencyName)) {
        this.notifications.push({
          info: "We recommend that you select from the list of known funding agency names.",
        });
      }
    },
    isNameFromCrossref: function (name) {
      return this.crossrefFundersNames.includes(name);
    },
    isDuplicateFunder: function (funderToCheck) {
      funderToCheck.agency_name = funderToCheck.agency_name || "";
      funderToCheck.agency_url = funderToCheck.agency_url || "";
      funderToCheck.award_number = funderToCheck.award_number || "";
      funderToCheck.award_title = funderToCheck.award_title || "";
      for (funder of this.fundingAgencies) {
        if (
          funder.agency_name == funderToCheck.agency_name &&
          funder.agency_url == funderToCheck.agency_url &&
          funder.award_number == funderToCheck.award_number &&
          funder.award_title == funderToCheck.award_title
        ) {
          return true;
        }
      }
      return false;
    },
    selectAgency: function (event) {
      this.isPending = false;
      this.crossrefSelected = true;
      this.currentlyEditing.agency_url = event.uri;
      this.checkAgency();
    },
    clearSelectedAgency: function () {
      this.crossrefSelected = false;
    },
    openAddModal() {
      this.mode = "Add";
      this.currentlyEditing = {};
      this.notifications = [];
      this.agencyName = "";
      // open source bug https://github.com/alexurquhart/vue-bootstrap-typeahead/issues/19
      this.$refs.agencyName.inputValue = "";
    },
    openEditModal(id) {
      this.mode = "Edit";
      this.notifications = [];
      const editingFundingAgency = this.fundingAgencies.filter((agency) => {
        return agency.agency_id == id;
      })[0];
      this.currentlyEditing = { ...editingFundingAgency };
      this.agencyName = this.currentlyEditing.agency_name;
      // open source bug https://github.com/alexurquhart/vue-bootstrap-typeahead/issues/19
      this.$refs.agencyName.inputValue = this.currentlyEditing.agency_name;
    },
    openDeleteModal(id) {
      this.currentlyDeleting = this.fundingAgencies.filter((agency) => {
        return agency.agency_id == id;
      })[0];
      this.deleteUrl = `/hsapi/_internal/${this.resourceId}/fundingagency/${id}/delete-metadata/`;
    },
  },
  watch: {
    agencyName: function (funder) {
      this.currentlyEditing.agency_name = funder;
      if (funder.length < this.MIN_SEARCH_LEN || this.crossrefSelected) {
        this.crossrefSelected = false; // reset
        return;
      }
      if (this.timeout) clearTimeout(this.timeout);
      this.timeout = setTimeout(() => {
        this.getCrossrefFunders(funder).then(()=>{
          this.checkAgency();
        })
      }, this.DEBOUNCE_API_MS);
    },
  },
  computed: {
    allowSubmit: function () {
      if (this.agencyName.trim() === "") return false;
      if (this.errorNotifications.length) return false;
      return true;
    },
    actionUri: function () {
      // Get the appropriate form action endpoint for either editing or adding funding agencies
      if (this.mode === "Edit") {
        return `/hsapi/_internal/${this.resourceId}/fundingagency/${this.currentlyEditing.agency_id}/update-metadata/`;
      } else {
        return `/hsapi/_internal/${this.resourceId}/fundingagency/add-metadata/`;
      }
    },
    errorNotifications: function () {
      return this.notifications.filter((notification) => {
        return "error" in notification;
      });
    },
    infoNotifications: function () {
      return this.notifications.filter((notification) => {
        return "info" in notification;
      });
    },
  },
});
