<template>
<!--  <div><input id="map-mode-button" type="button" class="mapdisp" value="Show Map" :disabled="!geoloaded"-->
<!--                v-on:click="displayMap">&lt;!&ndash; displayMap defined in map.js &ndash;&gt;<br/><br/>-->
    <div id="search" @keyup.enter="searchClick" class="input-group">
<!--        <input id="search-input" type="search" class="form-control" v-model="searchtext"-->
<!--               placeholder="Search all Public and Discoverable Resources">-->
<!--        <i id="search-clear" style="cursor:pointer" v-on:click="clearSearch"  class="fa fa-times-circle inside-right"></i>-->
<!--        <i id="search-glass" class="fa fa-search inside-left"></i>-->
        <vue-bootstrap-typeahead
            :data="autocomplete"
            v-model="searchtext"
            size="lg"
            :serializer="s => s"
            placeholder="Search..."
            @hit="selectedAddress = $event"
        />
      <br/>
        <select id="filterselect" v-model="searchcategory" @change="catsearch($event)" class="inside-right">
          <option>all</option>
          <option>abstract</option>
          <option>author</option>
          <option>subject</option>
          <option>owner</option>
          <option>contributor</option>
        </select>
<!--      <span>&nbsp; narrow matching</span>-->
    </div>
    <div id="resources-main" class="row">
      <div>
        <input type="radio" id="Discoverable" name="availability" value="discoverable" checked>
        <label for="Discoverable">Discoverable</label>
        <input type="radio" id="Public" name="availability" value="public">
        <label for="Public">Public</label>
        <input type="radio" id="Private" name="availability" value="private">
        <label for="Private">Private</label>
      </div>
        <div class="col-xs-12" id="resultsdisp">
            <br/>
<!--            <input id="map-filter-button" type="button" style="display:none" class="mapdisp" value="Filter by Map View" :disabled="!geoloaded" v-on:click="liveMapFilter" data-toggle="tooltip" title="Show list of resources that are located in the current map view">-->
<!--            Page: <input data-toggle="tooltip" title="Enter number or use Up and Down arrows" id="page-number" type="number"-->
<!--                min="1" max="9999" v-model="pagenum"> of {{Math.ceil(filteredResources.length / perpage)}}-->
<!--            | Showing: {{Math.min(perpage, resources.length, filteredResources.length)}} of {{filteredResources.length}} {{resgeotypes}}<br/>-->
        </div>
<!--        <div class="col-xs-3" id="facets">-->
<!--            <div id="filter-items">-->
<!--                &lt;!&ndash; filter by temporal overlap &ndash;&gt;-->
<!--                <div id="faceting-temporal">-->
<!--                            <h4 title="Enter a date range to filter search results by the timeframe that data was collected or observations were made">-->
<!--                                Filter by Date-->
<!--                            </h4>-->
<!--                        <div id="dateselectors" class="facet-list panel-collapse collapse in" aria-labelledby="headingDate">-->
<!--                            <date-pick-->
<!--                                 v-model="startdate"-->
<!--                                 :displayFormat="'MM/DD/YYYY'"-->
<!--                            ></date-pick><br/>-->
<!--                            <date-pick-->
<!--                                 v-model="enddate"-->
<!--                                 :displayFormat="'MM/DD/YYYY'"-->
<!--                            ></date-pick>-->
<!--                        </div>-->
<!--                </div>-->
<!--                &lt;!&ndash; filter by author &ndash;&gt;-->
<!--                <div id="faceting-creator">-->
<!--                    <div class="panel panel-default">-->
<!--                        <div id="headingAuthor" class="panel-heading">-->
<!--                            <h4 class="panel-title"><a data-toggle="collapse" href="#creator" aria-expanded="true" aria-controls="creator">-->
<!--                                Filter by Author</a>-->
<!--                            </h4>-->
<!--                        </div>-->
<!--                        <div id="creator" class="facet-list panel-collapse collapse in" aria-labelledby="headingAuthor">-->
<!--                            <ul class="list-group" id="list-group-creator">-->
<!--                                <li class="list-group-item" v-for="(author) in Object.keys(countAuthors).sort( (a, b) => a.toLowerCase().localeCompare(b.toLowerCase()))"-->
<!--                                    v-bind:key="author">-->
<!--                                    <span class="badge">{{countAuthors[author]}}</span><label class="checkbox noselect" :for="'author-'+author">{{author}}-->
<!--                                    <input type="checkbox" :value="author" class="faceted-selections"-->
<!--                                        v-model.lazy="authorFilter" :id="'author-'+author" @change="setAllMarkers">-->
<!--                                    </label>-->
<!--                                </li>-->
<!--                            </ul>-->
<!--                        </div>-->
<!--                    </div>-->
<!--                </div>-->
<!--                &lt;!&ndash; filter by owner &ndash;&gt;-->
<!--                <div id="faceting-owner">-->
<!--                    <div class="panel panel-default">-->
<!--                        <div id="headingOwner" class="panel-heading">-->
<!--                            <h4 class="panel-title"><a data-toggle="collapse" href="#owner" aria-expanded="true" aria-controls="owner">-->
<!--                                Filter by Owner</a>-->
<!--                            </h4>-->
<!--                        </div>-->
<!--                        <div id="owner" class="facet-list panel-collapse collapse in" aria-labelledby="headingOwner">-->
<!--                            <ul class="list-group" id="list-group-owner">-->
<!--                                <li class="list-group-item" v-for="(owner) in Object.keys(countOwners).sort( (a, b) => a.toLowerCase().localeCompare(b.toLowerCase()))"-->
<!--                                    v-bind:key="owner">-->
<!--                                    <span class="badge">{{countOwners[owner]}}</span>-->
<!--                                    <label class="checkbox noselect" :for="'owner-'+owner">{{owner}}-->
<!--                                        <input type="checkbox" class="faceted-selections" :value=owner-->
<!--                                            v-model.lazy="ownerFilter" :id="'owner-'+owner" @change="setAllMarkers">-->
<!--                                    </label>-->
<!--                                </li>-->
<!--                            </ul>-->
<!--                        </div>-->
<!--                    </div>-->
<!--                </div>-->
<!--                &lt;!&ndash; filter by subject &ndash;&gt;-->
<!--                <div id="faceting-subject">-->
<!--                    <div class="panel panel-default">-->
<!--                        <div id="headingSubject" class="panel-heading">-->
<!--                            <h4 class="panel-title"><a data-toggle="collapse" href="#subject" aria-expanded="true" aria-controls="subject">-->
<!--                                Filter by Subject</a>-->
<!--                            </h4>-->
<!--                        </div>-->
<!--                        <div id="subject" class="facet-list panel-collapse collapse in" aria-labelledby="headingSubject">-->
<!--                            <ul class="list-group" id="list-group-subject">-->
<!--                                <li class="list-group-item" v-for="(subject) in Object.keys(countSubjects).sort( (a, b) => a.toLowerCase().localeCompare(b.toLowerCase()))"-->
<!--                                    v-bind:key="subject">-->
<!--                                    <span class="badge">{{countSubjects[subject]}}</span>-->
<!--                                    <label class="checkbox noselect" :for="'subj-'+subject">{{subject}}-->
<!--                                        <input type="checkbox" class="faceted-selections" :value=subject-->
<!--                                           v-model.lazy="subjectFilter" :id="'subj-'+subject" @change="setAllMarkers">-->
<!--                                    </label>-->
<!--                                </li>-->
<!--                            </ul>-->
<!--                        </div>-->
<!--                    </div>-->
<!--                </div>-->
<!--                &lt;!&ndash; filter by contributor &ndash;&gt;-->
<!--                <div id="faceting-contributor">-->
<!--                    <div class="panel panel-default">-->
<!--                        <div id="headingContributor" class="panel-heading">-->
<!--                            <h4 class="panel-title"><a data-toggle="collapse" href="#contributor" aria-expanded="true" aria-controls="contributor">-->
<!--                                Filter by Contributor</a>-->
<!--                            </h4>-->
<!--                        </div>-->
<!--                        <div id="contributor" class="facet-list panel-collapse collapse in" aria-labelledby="headingContributor">-->
<!--                            <ul class="list-group" id="list-group-contributor">-->
<!--                                <li class="list-group-item" v-for="(contributor) in Object.keys(countContributors).sort( (a, b) => a.toLowerCase().localeCompare(b.toLowerCase()))"-->
<!--                                    v-bind:key="contributor">-->
<!--                                    <span class="badge">{{countContributors[contributor]}}</span>-->
<!--                                    <label class="checkbox noselect" :for="'contrib-'+contributor">{{contributor}}-->
<!--                                        <input type="checkbox" class="faceted-selections" :value=contributor-->
<!--                                            v-model.lazy="contributorFilter" :id="'contrib-'+contributor" @change="setAllMarkers">-->
<!--                                    </label>-->
<!--                                </li>-->
<!--                            </ul>-->
<!--                        </div>-->
<!--                    </div>-->
<!--                </div>-->
<!--                &lt;!&ndash; filter by type &ndash;&gt;-->
<!--                <div id="faceting-type">-->
<!--                    <div class="panel panel-default">-->
<!--                        <div id="headingType" class="panel-heading">-->
<!--                            <h4 class="panel-title"><a data-toggle="collapse" href="#type" aria-expanded="true" aria-controls="type">-->
<!--                                Filter by Type</a>-->
<!--                            </h4>-->
<!--                        </div>-->
<!--                        <div id="type" class="facet-list panel-collapse collapse in" aria-labelledby="headingType">-->
<!--                            <ul class="list-group" id="list-group-type">-->
<!--                                <li class="list-group-item" v-for="(type) in Object.keys(countTypes).sort()"-->
<!--                                    v-bind:key="type">-->
<!--                                    <span class="badge">{{countTypes[type]}}</span>-->
<!--                                    <label class="checkbox noselect" :for="'type-'+type">{{type}}-->
<!--                                        <input type="checkbox" class="faceted-selections" :value=type-->
<!--                                            v-model.lazy="typeFilter" :id="'type-'+type" @change="setAllMarkers">-->
<!--                                    </label>-->
<!--                                </li>-->
<!--                            </ul>-->
<!--                        </div>-->
<!--                    </div>-->
<!--                </div>-->
<!--                &lt;!&ndash; filter by availability &ndash;&gt;-->
<!--                <div id="faceting-availability">-->
<!--                    <div class="panel panel-default">-->
<!--                        <div id="headingAvailability" class="panel-heading">-->
<!--                            <h4 class="panel-title"><a data-toggle="collapse" href="#availability" aria-expanded="true" aria-controls="availability">-->
<!--                                Filter by Availability</a>-->
<!--                            </h4>-->
<!--                        </div>-->
<!--                        <div id="availability" class="facet-list panel-collapse collapse in" aria-labelledby="headingAvailability">-->
<!--                            <ul class="list-group" id="list-group-availability">-->
<!--                                <li class="list-group-item"-->
<!--                                    v-for="(availability) in Object.keys(countAvailabilities).sort()"-->
<!--                                    v-bind:key="availability">-->
<!--                                    <span class="badge">{{countAvailabilities[availability]}}</span>-->
<!--                                    <label class="checkbox noselect" :for="'avail-'+availability">{{availability}}-->
<!--                                        <input type="checkbox" class="faceted-selections" :value=availability-->
<!--                                            v-model.lazy="availabilityFilter" :id="'avail-'+availability" @change="setAllMarkers">-->
<!--                                    </label>-->
<!--                                </li>-->
<!--                            </ul>-->
<!--                        </div>-->
<!--                    </div>-->
<!--                </div>-->
<!--                &lt;!&ndash; end facet panels &ndash;&gt;-->
<!--            </div>-->
<!--        </div>-->
        <div id="resource-rows" class="col-lg-9">
            <br/>
            <div class="table-wrapper">
                <p id="map-message" style="display:none">Select area of interest on the map then click 'Filter by Map View'</p>
                <p v-if="(!filteredResources.length) && resloaded">Too many filter selections: no resources match those restrictions</p>
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
                            <img :src="resIconName[entry.type]" data-toggle="tooltip" style="cursor:pointer"
                                :title="entry.type" :alt="entry.type">
                            <img :src="entry.availabilityurl" data-toggle="tooltip" style="cursor:pointer"
                                :title="(entry.availability.toString().charAt(0).toUpperCase() + entry.availability.toString().slice(1))" :alt="entry.availability" :key="entry">
                        </td>
                        <td>
                          <a :href="entry.link" target="_blank" style="cursor:pointer" data-placement="top" data-toggle="tooltip"  :title="ellip(entry.abstract)" >{{entry.title}}</a>
                        </td>
                        <td>
                            <a :href="entry.author_link" data-toggle="tooltip" target="_blank" style="cursor:pointer"
                               :title="`Author: ${entry.author}

Owner: ${entry.owner}

Contributor: ${entry.contributor}`">{{entry.author}}</a>
<!-- Ensure the literal line above is not spaced or those spaces will appear in the tooltip -->
                        </td>
                        <!-- python is passing .isoformat() in views.py -->
                        <td style="cursor:pointer" data-toggle="tooltip" :title="new Date(entry.created).toLocaleTimeString('en-US')">{{new Date(entry.created).toLocaleDateString('en-US')}}</td>
                        <td style="cursor:pointer" data-toggle="tooltip" :title="new Date(entry.created).toLocaleTimeString('en-US')">{{new Date(entry.modified).toLocaleDateString('en-US')}}</td>
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
import VueBootstrapTypeahead from 'vue-bootstrap-typeahead';
import axios from 'axios'; // css font-size overridden in hs_discover/index.html to enforce 1em

export default {
  data() {
    return {
      autocomplete: [],
      searchcategory: 'all',
      resloaded: false,
      resources: [],
      searchtext: '',
      filterlimit: 10, // Minimum threshold for filter item to display with checkbox
      geodata: [],
      geopoints: [],
      startdate: 'Start Date',
      enddate: 'End Date',
      filteredcount: 0,
      perpage: 40, // resources per page
      pagenum: 1, // initial page number to show
      geoloaded: false, // searchjson endpoint called and retrieved geo data
      resgeotypes: '',
      googMarkers: [],
      uidFilter: [],
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
        Creator: 'creator', // contributor is stored as creator
        Title: 'title',
        Type: 'type',
        Subject: 'subject',
        Abstract: 'abstract',
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
    VueBootstrapTypeahead,
  },
  computed: {
    filteredResources() {
      // this routine typically completes in thousandths or hundredths of seconds with 3000 resources in Chrome
      let resfiltered = this.resources;
      if (this.uidFilter.length === 0 && this.authorFilter.length === 0 && this.ownerFilter.length === 0
          && this.subjectFilter.length === 0 && this.availabilityFilter.length === 0 && this.contributorFilter.length
          === 0 && this.typeFilter.length === 0) {
        // do nothing
      } else {
        // Filters should be most restrictive when two conflicting states are selected
        if (this.uidFilter.length > 0) {
          const resUids = resfiltered.filter(element => this.uidFilter.indexOf(element.short_id) > -1);
          resfiltered = resUids;
        }
        if (this.authorFilter.length > 0) {
          const resAuthors = resfiltered.filter(element => this.authorFilter.indexOf(element.author) > -1);
          resfiltered = resAuthors;
        }
        if (this.ownerFilter.length > 0) {
          const resOwners = resfiltered.filter(res => res.owner.filter(val => this.ownerFilter.includes(val))
            .length > 0);
          resfiltered = resOwners;
        }
        if (this.subjectFilter.length > 0) {
          const resSubjects = resfiltered.filter(res => res.subject.filter(val => this.subjectFilter.includes(val))
            .length > 0);
          resfiltered = resSubjects;
        }
        if (this.availabilityFilter.length > 0) {
          const resAvailabilities = resfiltered.filter(res => res.availability
            .filter(val => this.availabilityFilter.includes(val)).length > 0);
          resfiltered = resAvailabilities;
        }
        if (this.contributorFilter.length > 0) {
          const resContributors = resfiltered.filter(res => res.contributor.filter(val => this.contributorFilter.includes(val))
            .length > 0);
          resfiltered = resContributors;
        }

        if (this.typeFilter.length > 0) {
          const resTypes = resfiltered.filter(element => this.typeFilter.indexOf(element.type) > -1);
          resfiltered = resTypes;
        }
      }
      // if (this.startdate !== 'Start Date' && this.startdate !== '' && this.enddate !== 'End Date' && this.enddate !== '') {
      //   const resDate = [];
      //   resfiltered.forEach((item) => {
      //     if (item.start_date && item.end_date) {
      //       if (this.dateOverlap(item.start_date, item.end_date)) {
      //         resDate.push(item);
      //       }
      //     }
      //   });
      //   resfiltered = resDate;
      // }
      // resfiltered = this.columnSort(resfiltered);
      return resfiltered;
    },
  },
  watch: {
    resources() {
      this.populateFilters();
      if (this.resources.length > 0) {
        this.resloaded = true;
      } else {
        this.resloaded = false;
      }
    },
    geodata() {
      if (this.geodata.length > 0) {
        this.geoloaded = true;
      }
    },
    startdate() {
      this.setAllMarkers();
    },
    enddate() {
      this.setAllMarkers();
    },
  },
  mounted() {
    if (document.getElementById('qstring').value.trim() !== '') {
      this.searchtext = document.getElementById('qstring').value.trim();
    }
    this.searchClick();
    if (document.getElementById('map-view').style.display === 'block') {
      document.getElementById('map-filter-button').style.display = 'block';
    }
    this.experimentalGeo();
  },
  methods: {
    populateFilters() {
      this.countAuthors = this.filterBuilder(this.resources, 'author', this.filterlimit);
      this.countTypes = this.filterBuilder(this.resources, 'type');

      // this.countSubjects = this.filterMultiBuilder(this.resources, 'subject', this.filterlimit);
      let subjectbox = [];
      this.resources.forEach((res) => {
        subjectbox = subjectbox.concat(this.enumMulti(res.subject));
      });
      const csubjects = new this.Counter(subjectbox);
      this.countSubjects = Object.fromEntries(Object.entries(csubjects).filter(([v]) => v > this.filterlimit));

      let ownerbox = [];
      this.resources.forEach((res) => {
        ownerbox = ownerbox.concat(this.enumMulti(res.owner));
      });
      const cowners = new this.Counter(ownerbox);
      this.countOwners = Object.fromEntries(Object.entries(cowners).filter(([v]) => v > this.filterlimit));

      let contributorbox = [];
      this.resources.forEach((res) => {
        contributorbox = contributorbox.concat(this.enumMulti(res.contributor));
      });
      const ccontributors = new this.Counter(contributorbox);
      this.countContributors = Object.fromEntries(Object.entries(ccontributors).filter(([k, v]) => v > this.filterlimit));

      let availabilitybox = [];
      this.resources.forEach((res) => {
        availabilitybox = availabilitybox.concat(this.enumMulti(res.availability));
      });
      this.countAvailabilities = new this.Counter(availabilitybox);
    },
    searchClick() {
      const startd = new Date();
      document.body.style.cursor = 'wait';
      axios.get('/discoverapi/', { params: { q: this.searchtext, sort: this.sortingBy, asc: this.sortDir, cat: this.searchcategory } })
        .then((response) => {
          if (response) {
            try {
              this.resources = JSON.parse(response.data.resources);
              console.log(`/discoverapi/ call in: ${(new Date() - startd) / 1000} sec`);
              this.setAllMarkers();
              document.body.style.cursor = 'default';
            } catch (e) {
              console.log(`Error parsing discoverapi JSON: ${e}`);
              document.body.style.cursor = 'default';
            }
          }
        })
        .catch((error) => {
          console.error(`server /discoverapi/ error: ${error}`); // eslint-disable-line
          document.body.style.cursor = 'default';
        });
      this.pagenum = 1;
    },
    catsearch() {
      let subjects = [];
      const startd = new Date();
      axios.get('/discoverapi/', { params: { filter: this.searchcategory } })
        .then((response) => {
          if (response.status === 200) {
            subjects = JSON.parse(response.data.filter);
            console.log(`/discoverapi/ filter call in: ${(new Date() - startd) / 1000} sec`);
            this.autocomplete = subjects;
            console.log(subjects);
          } else {
            console.log(`Error: ${response.statusText}`);
          }
        })
        .catch((error) => {
          console.error(`server /discoverapi/ error: ${error}`); // eslint-disable-line
        });
    },
    clearSearch() {
      this.searchtext = '';
      this.cacheLoad();
    },
    experimentalGeo() {
      const startd = new Date();
      document.body.style.cursor = 'wait';
      axios.get('/discoverapi/', { params: { geo: 'load' } })
        .then((response) => {
          if (response) {
            try {
              this.geodata = JSON.parse(response.data.geo);
              console.log(`/discoverapi/ geo call in: ${(new Date() - startd) / 1000} sec`);
              this.setAllMarkers();
              this.geoloaded = true;
              document.body.style.cursor = 'default';
            } catch (e) {
              console.log(`Error parsing discoverapi JSON: ${e}`);
              this.geoloaded = false;
              document.body.style.cursor = 'default';
            }
          }
        })
        .catch((error) => {
          console.error(`server /discoverapi/ error: ${error}`); // eslint-disable-line
          this.geoloaded = false;
          document.body.style.cursor = 'default';
        });
      this.pagenum = 1;
    },
    loadgeo() {
      const startd = new Date();
      const geodata = [];
      axios.get('/searchjson/', { params: { data: {} } })
        .then((response) => {
          if (response.status === 200) {
            console.log(`/searchjson/ call in: ${(new Date() - startd) / 1000} sec`);
            response.data.forEach((item) => {
              const val = JSON.parse(item);
              if (val.coverage_type) {
                geodata.push(val);
              }
            });
            this.geodata = geodata;
          } else {
            console.log(`Error: ${response.statusText}`);
          }
        })
        .catch((error) => {
          console.error(`server /searchjson/ error: ${error}`); // eslint-disable-line
          this.geoloaded = false;
        });
    },
    filterBuilder(resources, thing, limit) {
      const box = [];

      try {
        resources.forEach(res => box.push(res[thing]));
      } catch (err) {
        console.log(`Type ${thing} not found when building filter: ${err}`);
      }
      const c = new this.Counter(box);
      if (limit) {
        try {
          return Object.fromEntries(Object.entries(c).filter(([v]) => v > limit));
        } catch (err) {
          console.log(`Could not truncate ${thing}: ${err}`);
          return c;
        }
      }
      return c;
    },
    filterMultiBuilder(resources, attribute, limit) {
      let box = [];
      resources.forEach((res) => {
        box = box.concat(this.enumMulti(res[attribute]));
      });
      const c = new this.Counter(box);
      if (limit) {
        return Object.fromEntries(Object.entries(c).filter(([v]) => v > limit));
      }
      return c;
    },
    columnSort(res) {
      if (this.sortingBy === 'created' || this.sortingBy === 'modified') {
        const datesorted = res.sort((a, b) => new Date(b[this.sortingBy]) - new Date(a[this.sortingBy]));
        return this.sortDir === -1 ? datesorted : datesorted.reverse();
      }
      Object.keys(res).forEach(key => (!res[key] ? delete res[key] : {})); // eslint-disable-line
      return res.sort((a, b) => ((a[this.sortingBy].toLowerCase() > b[this.sortingBy]
        .toLowerCase()) ? this.sortDir : -1 * this.sortDir));
    },
    sortBy(key) {
      if (this.sortMap[key] !== 'type') {
        this.sortDir = this.sortMap[key] === this.sortingBy ? this.sortDir * -1 : 1;
        this.sortingBy = this.sortMap[key];
        this.pagenum = 1;
        this.searchClick();
      }
    },
    sortStyling(key) {
      if (this.sortMap[key] === this.sortingBy) {
        return this.sortDir === 1 ? 'fa fa-fw fa-sort-asc' : 'fa fa-fw fa-sort-desc';
      }
      return this.sortMap[key] === 'type' ? '' : 'fa fa-fw fa-sort';
    },
    Counter(array) {
      // eslint-disable-next-line no-return-assign
      array.forEach(val => this[val] = (this[val] || 0) + 1);
    },
    doPager(res) {
      // return res.slice(0, this.perpage);
      const startx = (this.pagenum - 1) * this.perpage;
      return res.slice(startx, startx + this.perpage);
    },
    enumMulti(a) {
      let c = [];
      if (a) {
        c = Object.values(a);
      }
      return c;
    },
    ellip(input) {
      if (input) {
        return input.length > 500 ? `${input.substring(0, 500)}...` : input;
      }
      return '';
    },
    dateOverlap(dtstart, dtend) {
      // eslint-disable-next-line no-mixed-operators
      const ol = (Date.parse(dtstart) > Date.parse(this.startdate) && Date.parse(dtstart) < Date.parse(this.enddate) || Date.parse(this.startdate) > Date.parse(dtstart) && Date.parse(this.startdate) < Date.parse(dtend));
      console.log(`${dtstart} ${dtend} : ${this.startdate} ${this.enddate} : ${ol}`);
      return ol;
    },
    displayMap() {
      toggleMap(); // eslint-disable-line
      if (this.geoloaded) {
        this.setAllMarkers();
      }
      if (document.getElementById('map-view').style.display !== 'block') {
        this.uidFilter = [];
        document.getElementById('map-filter-button').style.display = 'none';
        document.getElementById('items-discovered').style.display = 'block';
        document.getElementById('map-message').style.display = 'none';
        document.getElementById('map-mode-button').value = 'Show Map';
        this.resgeotypes = '';
      } else if (document.getElementById('map-view').style.display === 'block') {
        document.getElementById('map-filter-button').style.display = 'block';
        document.getElementById('items-discovered').style.display = 'none';
        document.getElementById('map-message').style.display = 'block';
        document.getElementById('map-mode-button').value = 'Hide Map';
      }
    },
    setAllMarkers() {
      if (document.getElementById('map-view').style.display === 'block') {
        console.log('Rendering all markers');
        deleteMarkers(); // eslint-disable-line

        // TODO this code if we allow filtering in search to affect markers
        // const shids = this.filteredResources.map(x => x.short_id);
        // const geocoords = this.geodata.filter(element => shids.indexOf(element.short_id) > -1);
        // TODO for now just showing all geo
        const geocoords = this.geodata;

        let pts = geocoords.filter(x => x.coverage_type === 'point');
        const pointlocs = [];
        pts.forEach((x) => {
          if (!x.north || !x.east || Number.isNaN(parseFloat(x.north)) || Number.isNaN(parseFloat(x.east))) {
            console.log(`Bad geodata format ${x.short_id} ${x.north} ${x.east}`);
          } else if (Math.abs(parseFloat(x.north)) > 90 || Math.abs(parseFloat(x.east)) > 180) {
            console.log(`Bad geodata value ${x.short_id} ${x.north} ${x.east}`);
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
    liveMapFilter() {
      if (document.getElementById('map-view').style.display === 'block') {
        this.uidFilter = window.visMarkers;
        document.getElementById('items-discovered').style.display = 'block';
        document.getElementById('map-message').style.display = 'none';
        this.resgeotypes = 'with geographic coordinates';
      }
    },
    showHighlighter(hsid) {
      if (document.getElementById('map-view').style.display === 'block') {
        document.getElementById('topcontrol').click();
        highlightMarker(hsid); // eslint-disable-line
      }
    },
    renderMapSingle(pts) {
      pts.forEach((pt) => {
        if (pt.coverage_type === 'point') {
          createMarker({ lat: pt.north, lng: pt.east }, pt.title); // eslint-disable-line
        } else if (pt.coverage_type === 'box') {
          const lat = (parseInt(pt.northlimit, 10) + parseInt(pt.southlimit, 10)) / 2;
          const lng = (parseInt(pt.eastlimit, 10) + parseInt(pt.westlimit, 10)) / 2;
          console.log(pt.northlimit, pt.southlimit, pt.eastlimit, pt.westlimit);
          createMarker({ lat, lng }, pt.title); // eslint-disable-line
        }
      });
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
        margin-top: 0px;
    }
    .table-hover {
        margin-top: 0px;
    }
    .checkbox {

    }
    .mapdisp {
        right: 0px;
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
    #search {
        width: 850px;
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
    #filterselect {
      z-index: 999;
    }
</style>
