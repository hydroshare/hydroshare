<template>
  <div>
    <img v-bind:style="mapmode" v-b-tooltip.hover title="Viewing resources with geographic coordinates" alt="info" src="/static/img/info.png" height="15" width="15">
    <input id="map-mode-button" type="button" class="btn btn-default mapdisp" value="Show Map" :disabled="!geoloaded"
                v-on:click="showMap"><!-- displayMap defined in map.js -->
    <div id="search" @keyup.enter="searchClick" class="input-group">
        <input id="search-input" type="search" class="form-control" v-model="searchtext"
               placeholder="Search all Public and Discoverable Resources">
        <i id="search-clear" style="cursor:pointer" v-on:click="clearSearch"  class="fa fa-times-circle inside-right"></i>
        <i id="search-glass" class="fa fa-search inside-left"></i>
    </div>
    <div id="resources-main" class="row">
        <div v-if="resloaded" class="col-xs-12" id="resultsdisp">
            <br/>
            Page <input data-toggle="tooltip" title="Enter number or use Up and Down arrows" id="page-number" type="number" v-model="pagenum" @change="searchClick(true)"
                min="1" :max="pagecount"> of {{pagecount}}
              &nbsp;&nbsp;&nbsp;<b>\</b>&nbsp;&nbsp;&nbsp;Resources {{Math.max(0, pagedisp * perpage - perpage + 1)}} - {{Math.min(rescount, pagedisp * perpage)}} of {{rescount}}
             <br/>
        </div>
        <div class="col-xs-3" id="facets">
            <div id="filter-items">
                <!-- filter by temporal overlap -->
                <div id="faceting-temporal">
                    <div class="panel panel-default">
                        <div id="headingDate" class="panel-heading">
                            <h4 title="Enter a date range to filter search results by the timeframe that data was collected or observations were made"
                                class="panel-title"><a data-toggle="collapse" href="#dateselectors" aria-expanded="true" aria-controls="dateselectors">
                                Temporal Coverage Filter</a>
                            </h4>
                        </div>
                        <div id="dateselectors" class="facet-list panel-collapse collapse in" aria-labelledby="headingDate">
                            <date-pick
                                 v-model="startdate"
                                 :displayFormat="'MM/DD/YYYY'"
                            ></date-pick><br/>
                            <date-pick
                                 v-model="enddate"
                                 :displayFormat="'MM/DD/YYYY'"
                            ></date-pick>
                        </div>
                    </div>
                </div>
                <!-- filter by author -->
                <div id="faceting-creator">
                    <div class="panel panel-default">
                        <div id="headingAuthor" class="panel-heading">
                            <h4 class="panel-title"><a data-toggle="collapse" href="#creator" aria-expanded="true" aria-controls="creator">
                                Author Filter</a>
                            </h4>
                        </div>
                        <div id="creator" class="facet-list panel-collapse collapse in" aria-labelledby="headingAuthor">
                            <ul class="list-group" id="list-group-creator">
                                <li class="list-group-item" v-for="(author) in countAuthors"
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
                                Owner Filter</a>
                            </h4>
                        </div>
                        <div id="owner" class="facet-list panel-collapse collapse in" aria-labelledby="headingOwner">
                            <ul class="list-group" id="list-group-owner">
                                <li class="list-group-item" v-for="(owner) in countOwners"
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
                                Subject Filter</a>
                            </h4>
                        </div>
                        <div id="subject" class="facet-list panel-collapse collapse in" aria-labelledby="headingSubject">
                            <ul class="list-group" id="list-group-subject">
                                <li class="list-group-item" v-for="(subject) in countSubjects"
                                    v-bind:key="subject">
                                    <span class="badge">{{subject[1]}}</span>
                                    <label class="checkbox noselect" :for="'subj-'+subject[0]">{{subject[0]}}
                                        <input type="checkbox" class="faceted-selections" :value=subject[0]
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
                                Contributor Filter</a>
                            </h4>
                        </div>
                        <div id="contributor" class="facet-list panel-collapse collapse in" aria-labelledby="headingContributor">
                            <ul class="list-group" id="list-group-contributor">
                                <li class="list-group-item" v-for="(contributor) in countContributors"
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
                                Type Filter</a>
                            </h4>
                        </div>
                        <div id="type" class="facet-list panel-collapse collapse in" aria-labelledby="headingType">
                            <ul class="list-group" id="list-group-type">
                                <li class="list-group-item" v-for="(type) in countTypes"
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
                                Availability Filter</a>
                            </h4>
                        </div>
                        <div id="availability" class="facet-list panel-collapse collapse in" aria-labelledby="headingAvailability">
                            <ul class="list-group" id="list-group-availability">
                                <li class="list-group-item"
                                    v-for="(availability) in countAvailabilities"
                                    v-bind:key="availability">
                                    <span class="badge">{{availability[1]}}</span>
                                    <label class="checkbox noselect" :for="'avail-'+availability[0]">{{availability[0]}}
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
        <div id="resource-rows" class="col-lg-9">
            <br/>
            <div class="table-wrapper">
              <p class="table-message" style="color:red" v-if="(!resources.length) && (authorFilter.length ||
              ownerFilter.length || subjectFilter.length || contributorFilter.length || typeFilter.length ||
              availabilityFilter.length)"><i>No resource matches</i></p>
                <table id="items-discovered" v-if="resources.length"
                    class="table-hover table-striped resource-custom-table">
                    <thead>
                        <tr>
                            <th v-for="key in labels" v-bind:key="key" style="cursor:pointer"
                                @click="sortBy(key)">
                                <i :class="sortStyling(key)"></i>{{key}}
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                    <tr v-for="(entry) in resources" v-bind:key="entry">
                        <td>
                            <img :src="resIconName[entry.type]" v-b-tooltip.hover
                                :title="entry.type" :alt="entry.type">
                            <img :src="entry.availabilityurl" v-b-tooltip.hover
                                :title="(entry.availability.toString().charAt(0).toUpperCase() + entry.availability.toString().slice(1))" :alt="entry.availability" :key="entry">
                            <img v-if="entry.geo" src="/static/img/Globe-Green.png" height="25" width="25" v-b-tooltip.hover title="Mappable">
                        </td>
                        <td>
                            <a :href="entry.link" target="_blank" style="cursor:pointer" v-b-tooltip.hover :title="ellip(entry.abstract)" >{{entry.title}}</a>
                        </td>
                        <td>
                            <a :href="entry.author_link" v-b-tooltip.hover target="_blank"
                               :title="`(Owner): ${entry.owner} (Authors): ${nameList(entry.authors)} (Contributors): ${nameList(entry.contributor)}`">{{entry.author}}</a>
                        </td>
                        <!-- python is passing .isoformat() in views.py -->
                        <td v-b-tooltip.hover :title="new Date(entry.created).toLocaleTimeString('en-US')">{{new Date(entry.created).toLocaleDateString('en-US')}}</td>
                        <td v-b-tooltip.hover :title="new Date(entry.modified).toLocaleTimeString('en-US')">{{new Date(entry.modified).toLocaleDateString('en-US')}}</td>
                    </tr>
                    </tbody>
                </table>
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
      mapmode: 'display:none',
      resloaded: false,
      resources: [],
      searchtext: '',
      geodata: [],
      geopoints: [],
      startdate: 'Start Date',
      enddate: 'End Date',
      filteredcount: 0,
      rescount: 0,
      pagenum: 1, // initial page number to show
      pagedisp: 1, // page being displayed
      perpage: 0,
      pagecount: 0,
      geoloaded: true, // endpoint called and retrieved geo data for all resources
      googMarkers: [],
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
      sortDir: -1, // 1 asc -1 desc
      sortingBy: 'modified',
      resIconName: {
        'Composite Resource': '/static/img/resource-icons/composite48x48.png',
        Generic: '/static/img/resource-icons/generic48x48.png',
        'Geopgraphic Raster': '/static/img/resource-icons/geographicraster48x48.png',
        'Model Program Resource': '/static/img/resource-icons/modelprogram48x48.png',
        'Collection Resource': '/static/img/resource-icons/collection48x48.png',
        'Web App Resource': '/static/img/resource-icons/webapp48x48.png',
        'Time Series': '/static/img/resource-icons/timeseries48x48.png',
        'Script Resource': '/static/img/resource-icons/script48x48.png',
        'Model Instance Resource': '/static/img/resource-icons/modelinstance48x48.png',
        'SWAT Model Instance Resource': '/static/img/resource-icons/swat48x48.png',
        'MODFLOW Model Instance Resource': '/static/img/resource-icons/modflow48x48.png',
        'Multidimensional (NetCDF)': '/static/img/resource-icons/multidimensional48x48.png',
        'HIS Referenced Time Series': '/static/img/resource-icons/his48x48.png',
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
  props:
  ['columns', 'labels'],
  components: {
    datePick: DatePick,
  },
  computed: {
  },
  watch: {
    resources() {
      this.resloaded = this.resources.length > 0;
      if (this.mapmode === 'display:block') {
        this.setAllMarkers();
        gotoBounds(); // eslint-disable-line
      }
    },
    startdate() {
      this.searchClick();
    },
    enddate() {
      this.searchClick();
    },
    pagenum() {
      if (this.pagenum) {
        this.pagenum = Math.max(1, this.pagenum);
        this.pagenum = Math.min(this.pagenum, this.pagecount);
      }
    },
  },
  mounted() {
    if (document.getElementById('qstring').value.trim() !== '') {
      this.searchtext = document.getElementById('qstring').value.trim();
    }
    this.searchClick();
    this.filterBuilder();
  },
  methods: {
    searchClick(paging) { // paging flag to skip the page reset after data retrieval
      if (!this.pagenum) return; // user has cleared input box with intent do manually input an integer and subsequently caused a search event
      // const startd = new Date();
      document.body.style.cursor = 'wait';
      axios.get('/discoverapi/', {
        params: {
          q: this.searchtext,
          sort: this.sortingBy,
          asc: this.sortDir,
          cat: this.searchcategory,
          pnum: this.pagenum,
          filter: {
            author: this.authorFilter,
            owner: this.ownerFilter,
            subject: this.subjectFilter,
            contributor: this.contributorFilter,
            type: this.typeFilter,
            availability: this.availabilityFilter,
            date: [this.startdate, this.enddate],
            geofilter: this.mapmode === 'display:block',
          },
        },
      })
        .then((response) => {
          if (response) {
            try {
              this.resources = JSON.parse(response.data.resources);
              // console.log(`/discoverapi/ call in: ${(new Date() - startd) / 1000} sec`);
              if (paging !== true) {
                this.pagenum = 1;
              }
              this.pagecount = response.data.pagecount;
              this.rescount = response.data.rescount;
              this.perpage = response.data.perpage;
              this.pagedisp = this.pagenum;
              this.geodata = JSON.parse(response.data.geodata);
              document.body.style.cursor = 'default';
            } catch (e) {
              console.error(`Error parsing discoverapi JSON: ${e}`);
              document.body.style.cursor = 'default';
            }
          }
        })
        .catch((error) => {
          console.error(`server /discoverapi/ error: ${error}`); // eslint-disable-line
          document.body.style.cursor = 'default';
        });
    },
    clearSearch() {
      this.searchtext = '';
      this.searchClick();
    },
    filterBuilder() {
      // const startd = new Date();
      axios.get('/discoverapi/', {
        params: {
          filterbuilder: '1',
        },
      })
        .then((response) => {
          if (response) {
            try {
              // console.log(`/discoverapi/ filterbuilder call in: ${(new Date() - startd) / 1000} sec`);
              [this.countAuthors, this.countOwners, this.countSubjects, this.countContributors,
                this.countTypes, this.countAvailabilities] = JSON.parse(response.data.filterdata);
            } catch (e) {
              console.error(`Error parsing discoverapi JSON: ${e}`);
              document.body.style.cursor = 'default';
            }
          }
        })
        .catch((error) => {
          console.error(`server /discoverapi/ error: ${error}`); // eslint-disable-line
          document.body.style.cursor = 'default';
        });
    },
    sortBy(key) {
      if (this.sortMap[key] !== 'type') {
        this.sortDir = this.sortMap[key] === this.sortingBy ? this.sortDir * -1 : 1;
        this.sortingBy = this.sortMap[key];
        this.searchClick();
      }
    },
    sortStyling(key) {
      if (this.sortMap[key] === this.sortingBy) {
        return this.sortDir === 1 ? 'fa fa-fw fa-sort-asc' : 'fa fa-fw fa-sort-desc';
      }
      return this.sortMap[key] === 'type' ? '' : 'fa fa-fw fa-sort';
    },
    ellip(input) {
      if (input) {
        return input.length > 500 ? `${input.substring(0, 500)}...` : input;
      }
      return '';
    },
    nameList(names) {
      // console.log(names)
      try {
        return names.join(' | ');
      } catch {
        return names;
      }
    },
    showMap() {
      toggleMap(); // eslint-disable-line
      if (document.getElementById('map-view').style.display === 'block') {
        this.mapmode = 'display:block';
        this.setAllMarkers();
        document.getElementById('map-mode-button').value = 'Hide Map';
      } else if (document.getElementById('map-view').style.display !== 'block') {
        this.mapmode = 'display:none';
        document.getElementById('map-mode-button').value = 'Show Map';
      }
      this.searchClick();
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
            console.error(`Bad geodata format ${x.short_id} ${x.north} ${x.east}`);
          } else if (Math.abs(parseFloat(x.north)) > 90 || Math.abs(parseFloat(x.east)) > 180) {
            console.error(`Bad geodata value ${x.short_id} ${x.north} ${x.east}`);
          }
          const lat = Number.isNaN(parseFloat(x.north)) ? 0.0 : parseFloat(x.north);
          const lng = Number.isNaN(parseFloat(x.east)) ? 0.0 : parseFloat(x.east);
          pointlocs.push({ lat, lng });
        });
        const pointuids = pts.map(x => x.short_id);
        const pointlbls = pts.map(x => x.title);

        pts = geocoords.filter(x => x.coverage_type === 'region');
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
    #map-message {
       position: absolute;
       left: 110px;
    }
    #map-filter-button {
        margin-bottom: 12px;
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
    #filter-items {
        /* ensure collapse without overlap */
        width: 235px;
    }
    .table-wrapper {
        margin-top: 0;
    }
    .table-hover {
        margin-top: 0;
    }
    .checkbox {
        /*override older version of bootstrap styling*/
    }
    .mapdisp {
        right: 0;
        margin-top: 10px;
        margin-bottom: 20px;
    }
    .table-message {
        position: absolute;
        left: 100px;
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
        width: 100%;
        min-width: 800px;
        padding-left: 25px;
        padding-right: 25px;
        z-index: 1;
    }
    .inside-right {
        position: absolute;
        top: 10px;
        right: 20px;
        z-index: 2;
    }
    .inside-left {
        position: absolute;
        top: 10px;
        left: 10px;
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
</style>
