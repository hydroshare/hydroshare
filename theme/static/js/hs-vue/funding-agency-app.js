let fundingAgenciesApp = new Vue({
  el: "#funding-agency-app",
  delimiters: ["${", "}"],
  components: {
    VueBootstrapTypeahead,
  },
  data: {
    agencyNameInput: "", // current input for agency name search
    fundingAgencies: RES_FUNDING_AGENCIES, // funding agencies from the backend/Django
    unmatchedFunders: [], // funders not found in Crossref
    resourceId: SHORT_ID,
    resourceMode: RESOURCE_MODE, // edit/view
    selfAccessLevel: SELF_ACCESS_LEVEL, // user's access level on resource
    resPublished: RESOURCE_PUBLISHED_OR_UNDER_REVIEW,
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
    currentlyEditing: {}, // track the funder that we are editing
    startedEditing: {}, // store the funder that we started editing
    deleteUrl: "", // Django endpoint to call for deleting a funder
    currentlyDeleting: {}, // store the funder that we are deleting
  },
  mounted() {
    if (this.selfAccessLevel === "owner") {
      this.checkFunderNamesExistInCrossref(this.fundingAgencies);
    }
  },
  methods: {
    checkFunderNamesExistInCrossref: async function (funders) {
      try {
        const promises = [];
        for (const funder of funders) {
          promises.push(
            this.singleFunderNameExistsInCrossref(funder.agency_name)
          );
        }
        const results = await Promise.all(promises);
        const unmatched = results.filter((r)=>!r.match);
        for (let umatch of unmatched) {
          this.unmatchedFunders.push(umatch.funderName);
        }
        if (unmatched.length > 0){
          // In addition to a static warning in the Funding Agencies section for edit mode, also alert for resource owners regardles of view/edit mode
          this.showFundersAlert()
        }
      } catch (e) {
        console.error("Error while checking funder names in Crossref", e)
      }
    },
    showFundersAlert: function () {
      const message = 
        `The resource has the following funders listed that do not exist in the <a href="https://www.crossref.org/services/funder-registry" target="_blank">Open Funder Registry</a>:
        <br><strong>${this.unmatchedFunders.join("<br>")}</strong><br>
        We recommend updating the funders to conform to the <a href="https://www.crossref.org/services/funder-registry" target="_blank">Open Funder Registry</a> to ensure consistency and ease of reporting.
      `
      customAlert("Nonconforming Funders", message, "info", 10000, true);
    },
    singleFunderNameExistsInCrossref: async function (funderName) {
      let match = false
      const lowerFunderName = funderName.toLowerCase();
      const funders = await this.fetchFromCrossrefAPIFunderList(funderName);
      for (let funder of funders) {
        if (funder.name.toLowerCase() == lowerFunderName) match = true;
        for (let alt in funder["alt-names"]) {
          if (alt == lowerFunderName) match = true;
        }
      }
      return {funderName, match: match}
    },
    fetchFromCrossrefAPIFunderList: async function (funderName) {
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
    initCrossrefFundersSearch: async function (funderName) {
      if (funderName === "" || this.notifications.error) {
        return;
      }
      this.isPending = true;
      this.crossrefFunders = await this.fetchFromCrossrefAPIFunderList(
        funderName
      );
      if (this.crossrefFunders !== null) {
        this.crossrefFundersNames = this.crossrefFundersNames.concat(
          this.crossrefFunders.map((f) => f.name)
        );
      }
      this.isPending = false;
    },
    checkAgencyName: function () {
      this.notifications = [];

      if (this.agencyNameInput.trim() !== this.agencyNameInput) {
        this.notifications.push({
          error: "Agency name has leading or trailing whitespace.",
        });
      }

      if (this.agencyNameInput.length > 250) {
        this.notifications.push({
          error:
            "Agency name is too long. Ensure it has at most 250 characters.",
        });
      }

      if (this.isDuplicateFunder(this.currentlyEditing)) {
        if (this.mode == "Add") {
          this.notifications.push({
            error: "A funding agency matching these values already exists.",
          });
        }

        if (
          this.mode == "Edit" &&
          JSON.stringify(this.startedEditing) ===
            JSON.stringify(this.currentlyEditing)
        ) {
          this.notifications.push({
            error: "You haven't made any modifications yet.",
          });
        } else {
          this.notifications.push({
            error:
              "A funding agency other than the one you're editing already has these values.",
          });
        }
      }

      if (!this.isNameFromCrossref(this.agencyNameInput)) {
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
      this.checkAgencyName();
    },
    clearSelectedAgency: function () {
      this.crossrefSelected = false;
    },
    openAddModal() {
      this.mode = "Add";
      this.currentlyEditing = {};
      this.notifications = [];
      this.agencyNameInput = "";
      // open source bug https://github.com/alexurquhart/vue-bootstrap-typeahead/issues/19
      this.$refs.agencyNameInput.inputValue = "";
    },
    openEditModal(id) {
      this.mode = "Edit";
      this.notifications = [];
      const editingFundingAgency = this.fundingAgencies.filter((agency) => {
        return agency.agency_id == id;
      })[0];
      this.currentlyEditing = { ...editingFundingAgency };
      this.startedEditing = { ...editingFundingAgency };
      this.agencyNameInput = this.currentlyEditing.agency_name;
      // open source bug https://github.com/alexurquhart/vue-bootstrap-typeahead/issues/19
      this.$refs.agencyNameInput.inputValue = this.currentlyEditing.agency_name;
    },
    openDeleteModal(id) {
      this.currentlyDeleting = this.fundingAgencies.filter((agency) => {
        return agency.agency_id == id;
      })[0];
      this.deleteUrl = `/hsapi/_internal/${this.resourceId}/fundingagency/${id}/delete-metadata/`;
    },
  },
  watch: {
    agencyNameInput: function (funder) {
      this.currentlyEditing.agency_name = funder;
      if (funder.length < this.MIN_SEARCH_LEN || this.crossrefSelected) {
        this.crossrefSelected = false; // reset
        return;
      }
      this.checkAgencyName();
      if (this.timeout) clearTimeout(this.timeout);
      this.timeout = setTimeout(() => {
        this.initCrossrefFundersSearch(funder).then(() => {
          this.checkAgencyName();
        });
      }, this.DEBOUNCE_API_MS);
    },
  },
  computed: {
    allowSubmit: function () {
      if (this.agencyNameInput.trim() === "") return false;
      if (this.errorNotifications.length) return false;
      if (this.isPending) return false;
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
