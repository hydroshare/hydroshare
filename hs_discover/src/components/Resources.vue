<template>
    <div id="resources-main" class="row">
        <div class="col-xs-12" id="resultsdisp">
            <input type="number" v-model="pagenum">
            Page: {{pagenum}} of {{Math.ceil(filteredResources.length / perpage)}}
            Showing: {{Math.min(perpage, resources.length, filteredResources.length)}} of {{filteredResources.length}}
            <!-- toggleMap defined in map.js -->
            <input type="button" class="mapdisp" value="Toggle Map" :disabled="!geoloaded" v-on:click="displayMap">
            <input type="button" class="mapdisp" value="Update Map" :disabled="!geoloaded" v-on:click="setAllMarkers">
        </div>
        <div class="col-xs-3" id="facets">
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
                                Filter by Author</a>
                            </h4>
                        </div>
                        <div id="creator" class="facet-list panel-collapse collapse in" aria-labelledby="headingAuthor">
                            <ul class="list-group" id="list-group-creator">
                                <li class="list-group-item" v-for="(author) in Object.keys(countAuthors).sort( (a, b) => a.toLowerCase().localeCompare(b.toLowerCase()))"
                                    v-bind:key="author">
                                    <span class="badge">{{countAuthors[author]}}</span><label class="checkbox noselect" :for="'author-'+author">{{author}}
                                    <input type="checkbox" :value="author" class="faceted-selections"
                                        v-model="authorFilter" :id="'author-'+author">
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
                                Filter by Owner</a>
                            </h4>
                        </div>
                        <div id="owner" class="facet-list panel-collapse collapse in" aria-labelledby="headingOwner">
                            <ul class="list-group" id="list-group-owner">
                                <li class="list-group-item" v-for="(owner) in Object.keys(countOwners).sort( (a, b) => a.toLowerCase().localeCompare(b.toLowerCase()))"
                                    v-bind:key="owner">
                                    <span class="badge">{{countOwners[owner]}}</span>
                                    <label class="checkbox noselect" :for="'owner-'+owner">{{owner}}
                                        <input type="checkbox" class="faceted-selections" :value=owner
                                            v-model="ownerFilter" :id="'owner-'+owner">
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
                                Filter by Subject</a>
                            </h4>
                        </div>
                        <div id="subject" class="facet-list panel-collapse collapse in" aria-labelledby="headingSubject">
                            <ul class="list-group" id="list-group-subject">
                                <li class="list-group-item" v-for="(subject) in Object.keys(countSubjects).sort( (a, b) => a.toLowerCase().localeCompare(b.toLowerCase()))"
                                    v-bind:key="subject">
                                    <span class="badge">{{countSubjects[subject]}}</span>
                                    <label class="checkbox noselect" :for="'subj-'+subject">{{subject}}
                                        <input type="checkbox" class="faceted-selections" :value=subject
                                           v-model="subjectFilter" :id="'subj-'+subject">
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
                                Filter by Contributor</a>
                            </h4>
                        </div>
                        <div id="contributor" class="facet-list panel-collapse collapse in" aria-labelledby="headingContributor">
                            <ul class="list-group" id="list-group-contributor">
                                <li class="list-group-item" v-for="(contributor) in Object.keys(countContributors).sort( (a, b) => a.toLowerCase().localeCompare(b.toLowerCase()))"
                                    v-bind:key="contributor">
                                    <span class="badge">{{countContributors[contributor]}}</span>
                                    <label class="checkbox noselect" :for="'contrib-'+contributor">{{contributor}}
                                        <input type="checkbox" class="faceted-selections" :value=contributor
                                            v-model="contributorFilter" :id="'contrib-'+contributor">
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
                                Filter by Type</a>
                            </h4>
                        </div>
                        <div id="type" class="facet-list panel-collapse collapse in" aria-labelledby="headingType">
                            <ul class="list-group" id="list-group-type">
                                <li class="list-group-item" v-for="(type) in Object.keys(countTypes).sort()"
                                    v-bind:key="type">
                                    <span class="badge">{{countTypes[type]}}</span>
                                    <label class="checkbox noselect" :for="'type-'+type">{{type}}
                                        <input type="checkbox" class="faceted-selections" :value=type
                                            v-model="typeFilter" :id="'type-'+type">
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
                                Filter by Availability</a>
                            </h4>
                        </div>
                        <div id="availability" class="facet-list panel-collapse collapse in" aria-labelledby="headingAvailability">
                            <ul class="list-group" id="list-group-availability">
                                <li class="list-group-item"
                                    v-for="(availability) in Object.keys(countAvailabilities).sort()"
                                    v-bind:key="availability">
                                    <span class="badge">{{countAvailabilities[availability]}}</span>
                                    <label class="checkbox noselect" :for="'avail-'+availability">{{availability}}
                                        <input type="checkbox" class="faceted-selections" :value=availability
                                            v-model="availabilityFilter" :id="'avail-'+availability">
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
                <table v-if="filteredResources.length"
                    class="table-hover table-striped resource-custom-table" id="items-discovered">
                    <thead>
                        <tr>
                            <th v-for="key in labels" v-bind:key="key" style="cursor:pointer"
                                @click="sortBy(key)">
                                <i :class="sortStyling(key)"></i>{{key}}
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                    <tr v-for="entry in doPager(filteredResources)" v-bind:key="entry">
                        <td>
                            <img :src="resIconName[entry.type]" data-toggle="tooltip" style="cursor:pointer"
                                :title="entry.type" :alt="entry.type">
                            <img :src="entry.availabilityurl" data-toggle="tooltip" style="cursor:pointer"
                                :title="(entry.availability.toString().charAt(0).toUpperCase() + entry.availability.toString().slice(1))" :alt="entry.availability" :key="entry">
                            <img v-if="entry.shareable" src="/static/img/shareable.png" :alt="entry.shareable?'Shareable':'Not Shareable'"
                                data-toggle="tooltip" data-placement="right" :title="entry.shareable?'Shareable':'Not Shareable'"
                                style="cursor:pointer" data-original-title="Shareable">
                        </td>
                        <td>
                            <a :href="entry.link" data-toggle="tooltip" target="_blank" style="cursor:pointer"
                               :title="ellip(entry.abstract)" data-placement="top">{{entry.title}}</a>
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
</template>

<script>
import DatePick from 'vue-date-pick';
import 'vue-date-pick/dist/vueDatePick.css';
import axios from 'axios'; // css font-size overridden in hs_discover/index.html to enforce 1em

export default {
  data() {
    return {
      geodata: [],
      filterlimit: 10,
      geopoints: [],
      startdate: 'Start Date',
      enddate: 'End Date',
      filteredcount: 0,
      perpage: 40,
      pagenum: 1,
      geoloaded: false,
      resloaded: false, // track axios resource data promise after component mount
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
  ['resources', 'columns', 'labels'],
  components: {
    datePick: DatePick,
  },
  computed: {
    filteredResources() {
      // this routine typically completes in thousandths or hundredths of seconds with 3000 resources in Chrome
      const startd = new Date();
      if (this.resloaded) {
        let resfiltered = this.resources;
        if (this.authorFilter.length === 0 && this.ownerFilter.length === 0 && this.subjectFilter.length === 0 && this.availabilityFilter.length === 0 && this.contributorFilter.length === 0 && this.typeFilter.length === 0) {
          // do nothing
        } else {
          // Filters should be most restrictive when two conflicting states are selected
          if (this.authorFilter.length > 0) {
            const resAuthors = resfiltered.filter(element => this.authorFilter.indexOf(element.author) > -1);
            resfiltered = resAuthors;
          }
          if (this.ownerFilter.length > 0) {
            const resOwners = resfiltered.filter(element => this.ownerFilter.indexOf(element.owner) > -1);
            resfiltered = resOwners;
          }
          if (this.subjectFilter.length > 0) {
            const resSubjects = resfiltered.filter(res => res.subject.filter(val => this.subjectFilter.includes(val)).length > 0);
            resfiltered = resSubjects;
          }
          if (this.availabilityFilter.length > 0) {
            const resAvailabilities = resfiltered.filter(res => res.availability.filter(val => this.availabilityFilter.includes(val)).length > 0);
            resfiltered = resAvailabilities;
          }
          if (this.contributorFilter.length > 0) {
            const resContributors = resfiltered.filter(element => this.contributorFilter.indexOf(element.contributor) > -1);
            resfiltered = resContributors;
          }
          if (this.typeFilter.length > 0) {
            const resTypes = resfiltered.filter(element => this.typeFilter.indexOf(element.type) > -1);
            resfiltered = resTypes;
          }
        }
        if (this.startdate !== 'Start Date' && this.startdate !== '' && this.enddate !== 'End Date' && this.enddate !== '') {
          const resDate = [];
          resfiltered.forEach((item) => {
            if (item.start_date && item.end_date) {
              if (this.dateOverlap(item.start_date, item.end_date)) {
                resDate.push(item);
              }
            }
          });
          resfiltered = resDate;
        }
        resfiltered = this.columnSort(resfiltered);
        console.log(`filter compute: ${(new Date() - startd) / 1000}`);
        return resfiltered;
      }
      return [];
    },
  },
  mounted() {
    const startd = new Date();
    this.resloaded = this.resources.length > 0;
    this.countAuthors = this.filterBuilder(this.resources, 'author', this.filterlimit);
    this.countOwners = this.filterBuilder(this.resources, 'owner', this.filterlimit);
    this.countContributors = this.filterBuilder(this.resources, 'contributor', this.filterlimit);
    this.countTypes = this.filterBuilder(this.resources, 'type');

    let subjectbox = [];
    // res.subject is python list js array
    this.resources.forEach((res) => {
      subjectbox = subjectbox.concat(this.enumMulti(res.subject));
    });
    const csubjs = new this.Counter(subjectbox);
    this.countSubjects = Object.fromEntries(Object.entries(csubjs).filter(([k, v]) => v > this.filterlimit));

    let availabilitybox = [];
    // res.availability is python list js array
    this.resources.forEach((res) => {
      availabilitybox = availabilitybox.concat(this.enumMulti(res.availability));
    });
    this.countAvailabilities = new this.Counter(availabilitybox);
    console.log(`mount filter build: ${(new Date() - startd) / 1000}`);
    if (this.resloaded) { // update causes second mount
      this.loadGeo();
    }
  },
  methods: {
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
          return Object.fromEntries(Object.entries(c).filter(([k, v]) => v > limit));
        } catch (err) {
          console.log(`Could not truncate ${thing}: ${err}`);
          return c;
        }
      }
      return c;
    },
    columnSort(_res) {
      if (this.sortingBy === 'created' || this.sortingBy === 'modified') {
        const datesorted = _res.sort((a, b) => new Date(b[this.sortingBy]) - new Date(a[this.sortingBy]));
        return this.sortDir === -1 ? datesorted : datesorted.reverse();
      }
      Object.keys(_res).forEach(key => (!_res[key] ? delete _res[key] : {}));
      return _res.sort((a, b) => ((a[this.sortingBy].toLowerCase() > b[this.sortingBy].toLowerCase()) ? this.sortDir : -1 * this.sortDir));
    },
    sortBy(key) {
      if (this.sortMap[key] !== 'type') {
        this.sortDir = this.sortMap[key] === this.sortingBy ? this.sortDir * -1 : 1;
        this.sortingBy = this.sortMap[key];
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
    doPager(_res) {
      // return _res.slice(0, this.perpage);
      const startx = (this.pagenum - 1) * this.perpage;
      console.log(startx);
      return _res.slice(startx, startx + this.perpage);
    },
    enumMulti(a) {
      let c = [];
      if (a) {
        c = Object.values(a);
      }
      // const b = [];
      // c.forEach(x => b.push(x.split(',')));
      // const ret = [].concat.apply([], b);
      return c;
    },
    ellip(input) {
      if (input) {
        return input.length > 500 ? `${input.substring(0, 500)}...` : input;
      }
      return '';
    },
    dateOverlap(dtstart, dtend) {
      const ol = (Date.parse(dtstart) > Date.parse(this.startdate) && Date.parse(dtstart) < Date.parse(this.enddate) || Date.parse(this.startdate) > Date.parse(dtstart) && Date.parse(this.startdate) < Date.parse(dtend));
      console.log(`${dtstart} ${dtend} : ${this.startdate} ${this.enddate} : ${ol}`);
      return ol;
    },
    displayMap() {
      toggleMap();
      if (this.geoloaded) {
        this.setAllMarkers();
      }
    },
    setAllMarkers() {
      deleteMarkers();
      console.log(`num filtered res: ${this.filteredResources.length}`);
      const shids = this.filteredResources.map(x => x.short_id);
      const geopoints = this.geodata.filter(element => shids.indexOf(element.short_id) > -1);
      this.renderMap(geopoints);
    },
    loadGeo() {
      const startd = new Date();
      axios.get('/searchjson/', { params: { data: {} } })
        .then((response) => {
          if (response.status === 200) {
            console.log(`/searchjson/ call in: ${(new Date() - startd) / 1000} sec`);
            response.data.forEach((item) => {
              const val = JSON.parse(item);
              if (val.coverage_type) {
                this.geodata.push(val);
              }
            });
            this.geoloaded = true;
          } else {
            console.log(`Error: ${response.statusText}`);
            this.geoloaded = false;
          }
        })
        .catch((error) => {
          console.error(`server /searchjson/ error: ${error}`); // eslint-disable-line
          this.geoloaded = false;
        });
    },
    renderMapSingle(pts) {
      pts.forEach((pt) => {
        if (pt.coverage_type === 'point') {
          createMarker({ lat: pt.north, lng: pt.east }, pt.title);
        } else if (pt.coverage_type === 'box') {
          const lat = (parseInt(pt.northlimit, 10) + parseInt(pt.southlimit, 10)) / 2;
          const lng = (parseInt(pt.eastlimit, 10) + parseInt(pt.westlimit, 10)) / 2;
          console.log(pt.northlimit, pt.southlimit, pt.eastlimit, pt.westlimit);
          createMarker({ lat, lng }, pt.title);
        }
      });
    },
    renderMap(geos) {
      console.log(`rendering map: ${geos.length} locations`);
      const pts = geos.filter(x => x.coverage_type === 'point');
      const pointlocs = pts.map(x => Object.assign({ lat: x.north, lng: x.east }), {});
      const pointlinks = pts.map(x => `/resource/${x.short_id}`);
      const pointlbls = pts.map(x => x.title);
      createBatchMarkers(pointlocs, pointlinks, pointlbls);
    },
  },
};
</script>

<style scoped>
    @import url("https://maxcdn.bootstrapcdn.com/font-awesome/4.5.0/css/font-awesome.min.css");
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
</style>
