<template>
  <div id="discover-search" class="container">
    <input id="map-mode-button" type="button" class="btn btn-default mapdisp" value="Show Map" :disabled="!geoloaded"
        v-on:click="showMap">
    <div class="row">
      <div class="col col-sm col-md col-lg col-xl">
        <div id="search" class="input-group" @keyup.enter="searchClick(false, true, true)">
            <input id="search-input" class="form-control" type="search" v-model="searchtext"
                   placeholder="Search all Public and Discoverable Resources">
            <span id="search-clear" v-b-tooltip.hover title="Clear all selections and search again" style="cursor:pointer"
                  v-on:click="clearSearch"  class="fa fa-times-circle inside-right interactive"></span>
            <span id="search-glass" class="fa fa-search inside-left"></span>
            <p class="table-message" v-if="noMatches()">No resource matches</p>
            <a href="https://help.hydroshare.org/discovering-resources/discovering-data-and-models-from-hydroshare-users/field-based-search-in-discover/" target="_blank">Advanced search help</a>
        </div>
      </div>
    </div>
    <div id="resources-main" class="row">
        <!--  col 576 sm 768 md 992 lg 1200 xl -->
        <div class="col col-sm col-md-4 col-lg-3 col-xl-3" id="facets">
            <div id="filter-items">
                <!-- filter by temporal overlap -->
                <div id="faceting-temporal">
                    <div class="panel panel-default">
                        <div id="headingDate" class="panel-heading">
                            <h4 title="Enter a date range to filter search results by the timeframe that data was collected or observations were made"
                                class="panel-title"><a data-toggle="collapse" href="#dateselectors" aria-expanded="true" aria-controls="dateselectors">
                                Temporal Coverage</a>
                            </h4>
                        </div>
                        <div id="dateselectors" class="facet-list panel-collapse collapse in" aria-labelledby="headingDate">
<!--                          https://github.com/dbrekalo/vue-date-pick/issues/74  -->
                          <div class="date-wrapper">
                            <span class="fa fa-calendar calendar-icon"></span>
                              <date-pick style="width:167px"
                                 v-model="startdate"
                                 :displayFormat="'MM/DD/YYYY'"
                                 :inputAttributes="{placeholder: 'Start Date (M/D/YYYY)'}"
                            ></date-pick></div>
                          <div class="date-wrapper">
                            <span class="fa fa-calendar calendar-icon"></span>
                            <date-pick style="width:167px"
                                 v-model="enddate"
                                 :displayFormat="'MM/DD/YYYY'"
                                 :inputAttributes="{placeholder: 'End Date (M/D/YYYY)'}"
                            ></date-pick></div>
                        </div>
                    </div>
                </div>
                <!-- filter by author -->
                <div id="faceting-creator">
                    <div class="panel panel-default">
                        <div id="headingAuthor" class="panel-heading">
                            <h4 class="panel-title"><a data-toggle="collapse" href="#creator" aria-expanded="true" aria-controls="creator">
                                Author</a>
                            </h4>
                        </div>
                        <div id="creator" class="facet-list panel-collapse collapse in" aria-labelledby="headingAuthor">
                            <ul class="list-group" id="list-group-creator">
                                <li class="list-group-item" v-for="(author) in orderedFilter(countAuthors)"
                                    v-bind:key="author">
                                    <span class="badge">{{author[1]}}</span><label class="checkbox noselect" :for="'author-'+author[0]">{{author[0]}}
                                    <input type="checkbox" :value="author[0]" class="faceted-selections"
                                        v-model.lazy="authorFilter" :id="'author-'+author[0]" @change="searchClick">
                                    </label>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
                <!-- filter by owner -->
                <div id="faceting-owner">
                    <div class="panel panel-default">
                        <div id="headingOwner" class="panel-heading">
                            <h4 class="panel-title"><a data-toggle="collapse" href="#owner" aria-expanded="true" aria-controls="owner">
                                Owner</a>
                            </h4>
                        </div>
                        <div id="owner" class="facet-list panel-collapse collapse in" aria-labelledby="headingOwner">
                            <ul class="list-group" id="list-group-owner">
                                <li class="list-group-item" v-for="(owner) in orderedFilter(countOwners)"
                                    v-bind:key="owner">
                                    <span class="badge">{{owner[1]}}</span>
                                    <label class="checkbox noselect" :for="'owner-'+owner[0]">{{owner[0]}}
                                        <input type="checkbox" class="faceted-selections" :value=owner[0]
                                            v-model.lazy="ownerFilter" :id="'owner-'+owner[0]" @change="searchClick">
                                    </label>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
                <!-- filter by subject -->
                <div id="faceting-subject">
                    <div class="panel panel-default">
                        <div id="headingSubject" class="panel-heading">
                            <h4 class="panel-title"><a data-toggle="collapse" href="#subject" aria-expanded="true" aria-controls="subject">
                                Subject</a>
                            </h4>
                        </div>
                        <div id="subject" class="facet-list panel-collapse collapse in" aria-labelledby="headingSubject">
                            <ul class="list-group" id="list-group-subject">
                                <li class="list-group-item" v-for="(subject) in orderedFilter(countSubjects)"
                                    v-bind:key="subject">
                                    <span class="badge">{{subject[1]}}</span>
                                    <label class="checkbox noselect" :for="'subj-'+subject[0]">{{subject[0]}}
                                        <input type="checkbox" class="faceted-selections" :value=escJS(subject[0])
                                           v-model.lazy="subjectFilter" :id="'subj-'+subject[0]" @change="searchClick">
                                    </label>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
                <!-- filter by contributor -->
                <div id="faceting-contributor">
                    <div class="panel panel-default">
                        <div id="headingContributor" class="panel-heading">
                            <h4 class="panel-title"><a data-toggle="collapse" href="#contributor" aria-expanded="true" aria-controls="contributor">
                                Contributor</a>
                            </h4>
                        </div>
                        <div id="contributor" class="facet-list panel-collapse collapse in" aria-labelledby="headingContributor">
                            <ul class="list-group" id="list-group-contributor">
                                <li class="list-group-item" v-for="(contributor) in orderedFilter(countContributors)"
                                    v-bind:key="contributor">
                                    <span class="badge">{{contributor[1]}}</span>
                                    <label class="checkbox noselect" :for="'contrib-'+contributor[0]">{{contributor[0]}}
                                        <input type="checkbox" class="faceted-selections" :value=contributor[0]
                                            v-model.lazy="contributorFilter" :id="'contrib-'+contributor[0]" @change="searchClick">
                                    </label>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
                <!-- filter by type -->
                <div id="faceting-type">
                    <div class="panel panel-default">
                        <div id="headingType" class="panel-heading">
                            <h4 class="panel-title"><a data-toggle="collapse" href="#type" aria-expanded="true" aria-controls="type">
                                Content Type</a>
                            </h4>
                        </div>
                        <div id="type" class="facet-list panel-collapse collapse in" aria-labelledby="headingType">
                            <ul class="list-group" id="list-group-type">
                                <li class="list-group-item" v-for="(type) in orderedFilter(countTypes)"
                                    v-bind:key="type">
                                    <span class="badge">{{type[1]}}</span>
                                    <label class="checkbox noselect" :for="'type-'+type[0]">{{type[0]}}
                                        <input type="checkbox" class="faceted-selections" :value=type[0]
                                            v-model.lazy="typeFilter" :id="'type-'+type[0]" @change="searchClick">
                                    </label>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
                <!-- filter by availability -->
                <div id="faceting-availability">
                    <div class="panel panel-default">
                        <div id="headingAvailability" class="panel-heading">
                            <h4 class="panel-title"><a data-toggle="collapse" href="#availability" aria-expanded="true" aria-controls="availability">
                                Availability</a>
                            </h4>
                        </div>
                        <div id="availability" class="facet-list panel-collapse collapse in" aria-labelledby="headingAvailability">
                            <ul class="list-group" id="list-group-availability">
                                <li class="list-group-item"
                                    v-for="(availability) in orderedFilter(countAvailabilities)"
                                    v-bind:key="availability">
                                    <span class="badge">{{availability[1]}}</span>
                                    <label class="checkbox noselect" :for="'avail-'+availability[0]">
                                      {{availability[0].charAt(0).toUpperCase()+availability[0].slice(1)}}
                                        <input type="checkbox" class="faceted-selections" :value=availability[0]
                                            v-model.lazy="availabilityFilter" :id="'avail-'+availability[0]" @change="searchClick">
                                    </label>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
                <!-- end facet panels -->
            </div>
        </div>
        <div id="resource-rows" class="col-md col-lg">
            <div v-if="resources.length > 0" id="resultsdisp-upper">
            <span id="page-left-upper" style="cursor:pointer" v-on:click="paging(-1)" v-b-tooltip.hover title="Go back a page"
                class="pagination fa fa-angle-double-left fa-w-14 fa-fw fa-2x interactive"></span>
            Page <input v-b-tooltip.hover title="Enter number or use keyboard up and down arrows" id="page-number-upper"
                    type="number" v-model="pagenum" @change="searchClick(true)" min="1" :max="pagecount"> of {{pagecount}}
            <span id="page-right-upper" style="cursor:pointer" v-on:click="paging(1)" v-b-tooltip.hover title="Go forward a page"
                class="pagination fa fa-angle-double-right fa-w-14 fa-fw fa-2x interactive"></span>
                Resources {{Math.max(0, pagedisp * perpage - perpage + 1)}} - {{Math.min(rescount, pagedisp * perpage)}} of {{rescount}}
                  </div>
            <div class="table-wrapper">
                <table id="items-discovered" v-if="resources.length"
                    class="table-hover table-striped resource-custom-table main-table">
                    <thead>
                        <tr><th class="tbl-col-icons"><!-- placeholder --></th>
                            <th class="tbl-col-title" v-bind:key="'Title'" @click="sortBy('Title')">
                              <span class="interactive"><span :class="sortStyling('Title')"></span>Title</span>
                            </th>
                            <th class="tbl-col-authors" v-bind:key="'First Author'" @click="sortBy('First Author')">
                              <span class="interactive"><span :class="sortStyling('First Author')"></span>First<br>Author</span>
                            </th>
                            <th class="tbl-col-date" v-bind:key="'Date Created'" @click="sortBy('Date Created')">
                              <span class="interactive"><span :class="sortStyling('Date Created')"></span>Date<br>Created</span>
                            </th>
                              <th class="tbl-col-date" v-bind:key="'Last Modified'" @click="sortBy('Last Modified')">
                              <span class="interactive"><span :class="sortStyling('Last Modified')"></span>Last<br>Modified</span>
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                    <tr v-for="(entry) in resources" v-bind:key="entry">
                        <td class="tbl-col-icons">
                          <span id="img-icons">
                            <img :src="resIconName[entry.type]" v-b-tooltip.hover
                                :title="entry.type" :alt="entry.type" height="30" width="30">
                            <img :src="entry.availabilityurl" v-b-tooltip.hover
                                :title="(entry.availability.toString().charAt(0).toUpperCase() + entry.availability.toString().slice(1))" :alt="entry.availability" :key="entry">
                            <img v-if="entry.geo" src="/static/static/img/Globe-Green.png" height="25" width="25" v-b-tooltip.hover title="Contains Spatial Coverage">
                            </span>
                        </td>
                        <td class="tbl-col-title">
                          <a :href="entry.link" target="_blank" style="cursor:pointer" v-b-tooltip.hover :title="ellip(entry.abstract, 500)" >{{ellip(entry.title, 250)}}</a>
                        </td>
                        <td class="tbl-col-authors">
                            <a :href="entry.author_link" v-b-tooltip.hover target="_blank"
                               :title="`(AUTHORS): ${nameList(entry.authors)} (OWNERS): ${nameList(entry.owner)} (CONTRIBUTORS): ${nameList(entry.contributor)}`">{{entry.author}}</a>
                        </td>
                        <!-- python is passing .isoformat() in views.py -->
                      <td class="tbl-col-date"><span v-b-tooltip.hover :title="new Date(entry.created).toLocaleTimeString('en-US')">{{new Date(entry.created).toLocaleDateString('en-US')}}</span></td>
                      <td class="tbl-col-date"><span v-b-tooltip.hover :title="new Date(entry.modified).toLocaleTimeString('en-US')">{{new Date(entry.modified).toLocaleDateString('en-US')}}</span></td>
                    </tr>
                    </tbody>
                </table>
            </div>
                    <div v-if="resources.length > 15" id="resultsdisp-lower">
            <span id="page-left-lower" style="cursor:pointer" v-on:click="paging(-1)" v-b-tooltip.hover title="Go back a page"
                class="pagination fa fa-angle-double-left fa-w-14 fa-fw fa-2x interactive"></span>
            Page <input v-b-tooltip.hover title="Enter number or use keyboard up and down arrows" id="page-number-lower"
                    type="number" v-model="pagenum" @change="searchClick(true)" min="1" :max="pagecount"> of {{pagecount}}
            <span id="page-right-lower" style="cursor:pointer" v-on:click="paging(1)" v-b-tooltip.hover title="Go forward a page"
                class="pagination fa fa-angle-double-right fa-w-14 fa-fw fa-2x interactive"></span>
                Resources {{Math.max(0, pagedisp * perpage - perpage + 1)}} - {{Math.min(rescount, pagedisp * perpage)}} of {{rescount}}
            </div>
        </div>
    </div>
    </div>
</template>

<script>
import DatePick from 'vue-date-pick';
import 'vue-date-pick/dist/vueDatePick.css';
import axios from 'axios'; // css font-size overridden in hs_discover/index.html to enforce 1em

export default {
  data() {
    return {
      loading: true,
      prefiltered: false,
      columns: ['name', 'author', 'created', 'modified'],
      labels: ['Title', 'First Author', 'Date Created', 'Last Modified'],
      mapmode: 'display:none',
      resources: [],
      searchtext: '',
      geodata: [],
      geopoints: [],
      geoloaded: false, // do results contain any geodata
      googMarkers: [],
      startdate: '',
      enddate: '',
      filteredcount: 0,
      rescount: 0,
      pagenum: 1, // initial page number to show
      pagedisp: 1, // page being displayed
      perpage: 0,
      pagecount: 0,
      sortDir: -1, // 1 asc -1 desc
      sortingBy: 'modified',
      countAuthors: {},
      authorFilter: [],
      countSubjects: {},
      subjectFilter: [],
      countOwners: {},
      ownerFilter: [],
      countContributors: {},
      contributorFilter: [],
      countTypes: {},
      typeFilter: [],
      countAvailabilities: {},
      availabilityFilter: [],
      resIconName: {
        Resource: '/static/static/img/resource-icons/composite48x48.png',
        Collection: '/static/static/img/resource-icons/collection48x48.png',
        'App Connector': '/static/static/img/resource-icons/webapp48x48.png',
      },
      sortMap: {
        'First Author': 'author',
        Owner: 'owner',
        Creator: 'contributor',
        Title: 'title',
        Type: 'type',
        Subject: 'subject',
        'Date Created': 'created',
        'Last Modified': 'modified',
      },
    };
  },
  name: 'Resources',
  components: {
    datePick: DatePick,
  },
  computed: {
  },
  watch: {
    resources() {
      this.setAllMarkers();
      if (this.mapmode === 'display:block' && this.resources.length > 0) {
        gotoBounds(); // eslint-disable-line
      }
    },
    startdate() {
      if (this.enddate) {
        if (new Date(this.startdate) >= new Date(this.enddate)) {
          this.enddate = '';
        }
      }
      this.searchClick(false, false, false);
    },
    enddate() {
      if (this.startdate) {
        if (new Date(this.startdate) >= new Date(this.enddate)) {
          this.startdate = '';
        }
      }
      this.searchClick(false, false, false);
    },
    pagenum() {
      if (this.pagenum) {
        this.pagenum = Math.max(1, this.pagenum);
        this.pagenum = Math.min(this.pagenum, this.pagecount);
      }
    },
  },
  mounted() {
    // Allow manual querystring manipulation of freetext search via URL
    if (document.getElementById('qstring').value.trim() !== '') {
      this.searchtext = document.getElementById('qstring').value.trim();
      this.prefiltered = true;
    }
    // Allow exact subject search via URL particularly for Resource Landing Page
    const urlEncodedSubj = document.getElementById('prefillsubject').value.trim();
    if (urlEncodedSubj !== '') {
      this.subjectFilter = Array(decodeURIComponent(urlEncodedSubj));
      this.prefiltered = true;
    }
    if (this.subjectFilter) {
      const escaped = [];
      this.subjectFilter.forEach((x) => {
        escaped.push(x.replace(/\\/g, '\\\\'));
      });
      this.subjectFilter = escaped;
    }
    this.searchClick(false, true);
  },
  methods: {
    searchClick(paging, dofilters, reset) { // paging flag to skip the page reset after data retrieval
      if (!this.pagenum) return; // user has cleared input box with intent do manually input an integer and subsequently caused a search event
      document.body.style.cursor = 'wait';
      if (reset) {
        this.startdate = '';
        this.enddate = '';
        this.authorFilter = [];
        this.ownerFilter = [];
        this.subjectFilter = [];
        this.contributorFilter = [];
        this.typeFilter = [];
        this.availabilityFilter = [];
      }
      axios.get('/discoverapi/', {
        params: {
          q: this.searchtext,
          sort: this.sortingBy,
          asc: this.sortDir,
          cat: this.searchcategory,
          pnum: this.pagenum,
          filterbuilder: dofilters,
          updatefilters: dofilters,
          filter: JSON.stringify({
            author: this.authorFilter,
            owner: this.ownerFilter,
            subject: this.subjectFilter,
            contributor: this.contributorFilter,
            type: this.typeFilter,
            availability: this.availabilityFilter,
            date: this.getDates(),
            geofilter: this.mapmode === 'display:block',
          }),
        },
      })
        .then((response) => {
          if (response) {
            try {
              this.resources = JSON.parse(response.data.resources);
              if (paging !== true) {
                this.pagenum = 1;
              }
              this.pagecount = response.data.pagecount;
              this.rescount = response.data.rescount;
              this.perpage = response.data.perpage;
              this.pagedisp = this.pagenum;
              this.geodata = JSON.parse(response.data.geodata);
              if (this.geodata.length > 0) {
                this.geoloaded = true;
              }
              if (dofilters) {
                [this.countAuthors, this.countOwners, this.countSubjects, this.countContributors,
                  this.countTypes, this.countAvailabilities] = JSON.parse(response.data.filterdata);
              }
              document.body.style.cursor = 'default';
              this.loading = false;
            } catch (e) {
              document.body.style.cursor = 'default';
              this.loading = false;
            }
          }
        })
        .catch(() => {
          document.body.style.cursor = 'default';
          this.loading = false;
        });
    },
    clearSearch() {
      this.searchtext = '';
      this.searchClick(false, true, true);
    },
    paging(direction) {
      this.pagenum = Math.max(1, this.pagenum + Number.parseInt(direction, 10));
      this.searchClick(true);
    },
    orderedFilter(items) {
      if (items.length > 0) {
        return Object.values(items).sort((a, b) => a[0].toLowerCase().localeCompare(b[0].toLowerCase()));
      }
      return [];
    },
    sortBy(key) {
      if (this.sortMap[key] !== 'type') {
        this.sortDir = this.sortMap[key] === this.sortingBy ? this.sortDir * -1 : 1;
        this.sortingBy = this.sortMap[key];
        this.searchClick(true);
      }
    },
    sortStyling(key) {
      if (this.sortMap[key] === this.sortingBy) {
        return this.sortDir === 1 ? 'fa fa-fw fa-sort-asc interactive' : 'fa fa-fw fa-sort-desc interactive';
      }
      return this.sortMap[key] === 'type' ? '' : 'fa fa-fw fa-sort interactive';
    },
    getDates() {
      if (this.startdate === '' && this.enddate === '') {
        return [];
      }
      return [this.startdate !== '' ? this.startdate : new Date('1/1/1900').toISOString().split('T')[0],
        this.enddate !== '' ? this.enddate : new Date().toISOString().split('T')[0]];
    },
    ellip(input, size) {
      if (input && size) {
        return input.length > size ? `${input.substring(0, size)}...` : input;
      }
      return '';
    },
    escJS(input) {
      return input.replace(/\\/g, '\\\\');
    },
    nameList(names) {
      try {
        return names.join(' | ');
      } catch {
        return names;
      }
    },
    noMatches() {
      return (!this.loading) && (!this.resources.length) && (this.authorFilter.length || this.ownerFilter.length
          || this.subjectFilter.length || this.contributorFilter.length || this.typeFilter.length
          || this.availabilityFilter.length || this.searchtext !== '' || this.startdate !== '' || this.enddate !== '');
    },
    showMap() {
      toggleMap(); // eslint-disable-line
      if (document.getElementById('map-view').style.display === 'block') {
        this.mapmode = 'display:block';
        if (this.resources.length > 0) {
          this.searchClick(false, false, false);
          this.setAllMarkers();
        } else {
          this.setAllMarkers();
          recenterMap(); // eslint-disable-line
        }
        document.getElementById('map-mode-button').value = 'Hide Map';
      } else if (document.getElementById('map-view').style.display !== 'block') {
        this.mapmode = 'display:none';
        document.getElementById('map-mode-button').value = 'Show Map';
        this.searchClick(false, false, false);
      }
    },
    setAllMarkers() {
      const all = false;
      if (document.getElementById('map-view').style.display === 'block') {
        deleteMarkers(); // eslint-disable-line
        let geocoords = this.geodata;
        if (!all) {
          const shids = this.resources.map(x => x.short_id);
          geocoords = this.geodata.filter(element => shids.indexOf(element.short_id) > -1);
        }
        let pts = geocoords.filter(x => x.coverage_type === 'point');
        const pointlocs = [];
        pts.forEach((x) => {
          if (!x.north || !x.east || Number.isNaN(parseFloat(x.north)) || Number.isNaN(parseFloat(x.east))) {
            // no action
          } else if (Math.abs(parseFloat(x.north)) > 90 || Math.abs(parseFloat(x.east)) > 180) {
            // no action
          }
          const lat = Number.isNaN(parseFloat(x.north)) ? 0.0 : parseFloat(x.north);
          const lng = Number.isNaN(parseFloat(x.east)) ? 0.0 : parseFloat(x.east);
          pointlocs.push({ lat, lng });
        });
        const pointuids = pts.map(x => x.short_id);
        const pointlbls = pts.map(x => x.title);

        pts = geocoords.filter(x => x.coverage_type === 'box');
        const regionlocs = [];
        pts.forEach((x) => {
          const eastlim = Number.isNaN(parseFloat(x.eastlimit)) ? 0.0 : parseFloat(x.eastlimit);
          const westlim = Number.isNaN(parseFloat(x.westlimit)) ? 0.0 : parseFloat(x.westlimit);
          const northlim = Number.isNaN(parseFloat(x.northlimit)) ? 0.0 : parseFloat(x.northlimit);
          const southlim = Number.isNaN(parseFloat(x.southlimit)) ? 0.0 : parseFloat(x.southlimit);
          const lat = (northlim + southlim) / 2;
          const lng = (eastlim + westlim) / 2;
          if (eastlim !== 0 && westlim !== 0 && northlim !== 0 && southlim !== 0) {
            regionlocs.push({ lat, lng });
          }
        });
        const regionuids = pts.map(x => x.short_id);
        const regionlbls = pts.map(x => x.title);

        createBatchMarkers(pointlocs.concat(regionlocs), pointuids.concat(regionuids), pointlbls.concat(regionlbls)); // eslint-disable-line
      }
    },
  },
};
</script>

<style scoped>
    @import url("https://maxcdn.bootstrapcdn.com/font-awesome/4.5.0/css/font-awesome.min.css");
    #discover-search.container {
        padding: 0;
    }
    #resultsdisp {
        left: 300px;
    }
    #page-number {
        width: 60px;
    }
    #wrapper .search-field div {
        width: 100%;
    }
    #wrapper > a {
        margin-left: 1em;
    }
    #search input {
        padding-left: 30px;
        padding-right: 30px;
        z-index: 1;
    }
    #img-icons {
        min-width: 85px;
        white-space: nowrap;
    }
    #page-right-upper, #page-right-lower {
        margin-right: 25px;
    }
    #page-number-upper, #page-number-lower {
        border-style: solid;
        border-width: 1px;
        border-color: #ccc;
        outline: none;
        width: 55px;
    }
    .main-table {
        width: 100%;
    }
    .panel-title > a:before {
        float: left !important;
        font-family: FontAwesome;
        content:"\f068";
        padding-right: 5px;
    }
    .panel-title > a.collapsed:before {
        float: left !important;
        content:"\f067";
    }
    .panel-title > a:hover,
    .panel-title > a:active,
    .panel-title > a:focus  {
        text-decoration:none;
    }
    .table-wrapper {
        margin-top: 0;
    }
    .table-hover {
        margin-top: 0;
    }
    .checkbox {
        /* Override older version of bootstrap styling */
    }
    .mapdisp {
        right: 0;
        margin-top: 10px;
        margin-bottom: 20px;
    }
    .table-message {
        font-style: italic;
        color:red;
    }
    .tbl-col-icons {
        width: 100px;
        max-width: 100px;
        padding-left: 5px;
        padding-right: 0;
    }
    .tbl-col-title {
        min-width: 150px;
        max-width: 440px;
        word-break: keep-all;
        word-wrap: anywhere;
        text-overflow: ellipsis;
        overflow: hidden;
        white-space: normal;
        padding-top: 4px;
        padding-bottom: 4px;
    }
    .tbl-col-authors {
        min-width: 110px;
        max-width: 120px;
        word-break: normal;
        word-wrap: break-word;
    }
    .tbl-col-date {
        min-width: 94px;
        max-width: 94px;
        word-break: break-all;
        word-wrap: break-word;
    }
    .title-span {
        min-width: 437px;
        max-width: 437px;
        width: 437px;
        word-break: normal;
        word-wrap: break-word;
        white-space: normal;
        padding-top: 4px;
        padding-bottom: 4px;
    }
    .inside-right {
        position: absolute;
        top: 10px;
        right: 12px;
        z-index: 2;
    }
    .inside-left {
        position: absolute;
        top: 10px;
        left: 12px;
        z-index: 2;
    }
    .btn.focus {
        /* Remove unwanted outline behavior */
        outline: 0;
        box-shadow: None;
    }
    .btn:focus {
        /* Remove unwanted outline behavior */
        outline: 0;
        box-shadow: None;
    }
    .date-wrapper {
        display: block;
        width: 100%;
        border-style: solid;
        border-width: 1px;
        border-color: #ccc;
    }
    .calendar-icon {
        margin: 6px 6px 6px 9px;
    }
    .pagination {
      z-index: 1000;
      margin-top: 15px;
      margin-bottom: 15px;
      transform: translateY(4px);
    }
    .interactive:hover {
      color: LightBlue;
      cursor: pointer;
      /* Avoid double-click selection during rapid clicking: */
      user-select: none; /* standard syntax */
      -webkit-user-select: none; /* webkit (safari, chrome) browsers */
      -moz-user-select: none; /* mozilla browsers */
      -ms-user-select: none; /* IE10+ */
    }
</style>
