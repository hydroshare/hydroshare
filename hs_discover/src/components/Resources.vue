<template>
    <div id="resources-main" class="row">
        <div class="col-xs-12" id="resultsdisp">
            Showing: {{Math.min(displen, resources.length)}} of {{resources.length}}
            <input type="number" v-model="displen" data-toggle="tooltip"
                            title="values over 500 may make operations sluggish">
            <!-- toggleMap defined in map.js -->
            <input type="button" class="mapdisp" value="Toggle Map" v-on:click="displayMap">
            <input type="button" class="mapdisp" value="Update Map" v-on:click="setAllMarkers">
        </div>
        <div class="col-sm-3 col-xs-12" id="facets">
            <div id="filter-items">
                <!-- filter by temporal overlap -->
                <div id="faceting-temporal">
                    <div class="panel panel-default">
                        <div class="panel-heading">
                            <h4 data-toggle="tooltip" title="Enter a date range to filter search results by the timeframe that data was collected or observations were made"
                                class="panel-title">
                                <i class="fa fa-window-minimize" aria-hidden="true" data-toggle="collapse" href="#dateselectors" role="button" aria-expanded="false" aria-controls="dateselectors"></i>
                                Temporal Coverage</h4>
                        </div>
                        <div id="dateselectors" class="facet-list panel-collapse collapse in">
                            From
                            <date-pick
                                 v-model="startdate"
                                 :displayFormat="'MM/DD/YYYY'"
                            ></date-pick><br/>
                            To
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
                        <div class="panel-heading">
                            <h4 class="panel-title">
                                <i class="fa fa-window-minimize" aria-hidden="true" data-toggle="collapse" href="#creator" role="button" aria-expanded="false" aria-controls="creator"></i>
                                Filter by author</h4>
                        </div>
                        <div id="creator" class="facet-list panel-collapse collapse in">
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
                        <div class="panel-heading">
                            <h4 class="panel-title">
                                <i class="fa fa-window-minimize" aria-hidden="true" data-toggle="collapse" href="#owner" role="button" aria-expanded="false" aria-controls="owner"></i>
                                Filter by owner</h4>
                        </div>
                        <div id="owner" class="facet-list panel-collapse collapse in">
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
                        <div class="panel-heading">
                            <h4 class="panel-title">
                                <i class="fa fa-window-minimize" aria-hidden="true" data-toggle="collapse" href="#subject" role="button" aria-expanded="false" aria-controls="subject"></i>
                                Filter by subject</h4>
                        </div>
                        <div id="subject" class="facet-list panel-collapse collapse in">
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
                        <div class="panel-heading">
                            <h4 class="panel-title">
                                <i class="fa fa-window-minimize" aria-hidden="true" data-toggle="collapse" href="#contributor" role="button" aria-expanded="false" aria-controls="contributor"></i>
                                Filter by contributor</h4>
                        </div>
                        <div id="contributor" class="facet-list panel-collapse collapse in">
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
                        <div class="panel-heading">
                            <h4 class="panel-title">
                                <i class="fa fa-window-minimize" aria-hidden="true" data-toggle="collapse" href="#type" role="button" aria-expanded="false" aria-controls="type"></i>
                                Filter by type</h4>
                        </div>
                        <div id="type" class="facet-list panel-collapse collapse in">
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
                        <div class="panel-heading">
                            <h4 class="panel-title">
                                <i class="fa fa-window-minimize" aria-hidden="true" data-toggle="collapse" href="#availability" role="button" aria-expanded="false" aria-controls="availability"></i>
                                Filter by availability</h4>
                        </div>
                        <div id="availability" class="facet-list panel-collapse collapse in">
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
        <div id="resource-rows" class="col-sm-9 col-xs-12">
            <br/>
            <div class="table-wrapper">
                <table v-if="filteredResources.length"
                    class="table-hover table-striped resource-custom-table" id="items-discovered">
                    <thead>
                        <tr>
                            <th v-for="key in labels" v-bind:key="key"
                                @click="sortBy(key)">
                                <i :class="sortStyling(key)"></i>{{key}}
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                    <tr v-for="entry in filteredResources" v-bind:key="entry">
                        <td>
                            <img :src="resIconName[entry.type]" data-toggle="tooltip"
                                :title="entry.type" :alt="entry.type">
                            <img :src="entry.availabilityurl" data-toggle="tooltip"
                                :title="entry.availability" :alt="entry.availability" :key="entry">
                            <img v-if="entry.shareable" src="/static/img/shareable.png" :alt="entry.shareable?'Shareable':'Not Shareable'"
                                data-toggle="tooltip" data-placement="right" :title="entry.shareable?'Shareable':'Not Shareable'"
                                data-original-title="Shareable">
                        </td>
                        <td>
                            <a :href="entry.link" data-toggle="tooltip"
                               :title="ellip(entry.abstract)" data-placement="top">{{entry.title}}</a>
                        </td>
                        <td>
                            <a :href="entry.author_link" data-toggle="tooltip"
                               :title="`Author: ${entry.author} | Owner: ${entry.owner} | Contributor: ${entry.contributor}`">{{entry.author}}</a>
                        </td>
                        <!-- python is passing .isoformat() in views.py -->
                        <td data-toggle="tooltip" :title="new Date(entry.created).toLocaleTimeString('en-US')">{{new Date(entry.created).toLocaleDateString('en-US')}}</td>
                        <td data-toggle="tooltip" :title="new Date(entry.created).toLocaleTimeString('en-US')">{{new Date(entry.modified).toLocaleDateString('en-US')}}</td>
                    </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</template>

<script>
import DatePick from 'vue-date-pick';
import 'vue-date-pick/dist/vueDatePick.css'; // css font-size overridden in hs_discover/index.html to enforce 1em

export default {
  data() {
    return {
      geopoints: [],
      startdate: 'Start Date',
      enddate: 'End Date',
      displen: 50,
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
      sortDir: 1, // 1 asc -1 desc
      sortingBy: 'modified',
      resIconName: {
        'Composite Resource': '/static/img/resource-icons/composite48x48.png',
        Generic: '/static/img/resource-icons/generic48x48.png',
        'Geopgraphic Raster': '/static/img/resource-icons/geographicraster48x48.png',
        'Model Program Resource': '/static/img/resource-icons/modelprogram48x48.png',
        'Collection Resource': '/static/img/resource-icons/collection48x48.png',
        'Web App Resource': '/static/img/resource-icons/webapp48x48.png',
        'Time Series': '/static/img/resource-icons/timeseries48x48.png',
        'Model Instance Resource': '/static/img/resource-icons/modelinstance48x48.png',
        'SWAT Model Instance Resource': '/static/img/resource-icons/swat48x48.png',
        'MODFLOW Model Instance Resource': '/static/img/resource-icons/modflow48x48.png',
        'Multidimensional (NetCDF)': '/static/img/resource-icons/multidimensional48x48.png',
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
  ['resources', 'geodata', 'columns', 'labels'],
  components: {
    datePick: DatePick,
  },
  computed: {
    // additiveFilteredResources() {
    //   if (this.resloaded) {
    //     if (this.authorFilter.length === 0 && this.ownerFilter.length === 0 && this.subjectFilter.length === 0 && this.availabilityFilter.length === 0 && this.contributorFilter.length === 0 && this.typeFilter.length === 0) {
    //       return this.resources;
    //     }
    //     const resfiltered = [];
    //     const resAuthors = this.resources.filter(element => this.authorFilter.indexOf(element.author) > -1);
    //     resAuthors.forEach((item) => {
    //       if (!resfiltered.includes(item)) {
    //         resfiltered.push(item);
    //       }
    //     });
    //     const resOwners = this.resources.filter(element => this.ownerFilter.indexOf(element.owner) > -1);
    //     resOwners.forEach((item) => {
    //       if (!resfiltered.includes(item)) {
    //         resfiltered.push(item);
    //       }
    //     });
    //     const resSubjects = this.resources.filter(res => res.subject.filter(val => this.subjectFilter.includes(val)).length > 0);
    //     resSubjects.forEach((item) => {
    //       if (!resfiltered.includes(item)) {
    //         resfiltered.push(item);
    //       }
    //     });
    //     const resAvailabilities = this.resources.filter(res => res.availability.filter(val => this.availabilityFilter.includes(val)).length > 0);
    //     resAvailabilities.forEach((item) => {
    //       if (!resfiltered.includes(item)) {
    //         resfiltered.push(item);
    //       }
    //     });
    //     const resContributors = this.resources.filter(element => this.contributorFilter.indexOf(element.contributor) > -1);
    //     resContributors.forEach((item) => {
    //       if (!resfiltered.includes(item)) {
    //         resfiltered.push(item);
    //       }
    //     });
    //     const resTypes = this.resources.filter(element => this.typeFilter.indexOf(element.type) > -1);
    //     resTypes.forEach((item) => {
    //       if (!resfiltered.includes(item)) {
    //         resfiltered.push(item);
    //       }
    //     });
    //     if (this.sortingBy === 'created' || this.sortingBy === 'modified') {
    //       const datesorted = resfiltered.sort((a, b) => new Date(b[this.sortingBy]) - new Date(a[this.sortingBy]));
    //       return this.sortDir === -1 ? datesorted : datesorted.reverse();
    //     }
    //     return resfiltered.sort((a, b) => ((a[this.sortingBy].toLowerCase() > b[this.sortingBy].toLowerCase()) ? this.sortDir : -1 * this.sortDir));
    //   }
    //   return [];
    // },
    filteredResources() {
      document.body.style.cursor = 'wait';
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
        if (this.startdate !== 'Start Date' && this.startdate !== '') {
          const resStartDate = [];
          resfiltered.forEach((item) => {
            if (item.start_date) {
              console.log(`has a start date ${item.start_date}`);
              if (item.start_date >= this.startdate) {
                console.log(`including date ${item.start_date}`);
                resStartDate.push(item);
              }
            }
          });
          resfiltered = resStartDate;
        }
        if (this.enddate !== 'End Date' && this.enddate !== '') {
          const resEndDate = [];
          resfiltered.forEach((item) => {
            if (item.end_date) {
              console.log(`has an end date ${item.end_date}`);
              if (item.end_date <= this.enddate) {
                console.log(`including date ${item.end_date}`);
                resEndDate.push(item);
              }
            }
          });
          resfiltered = resEndDate;
        }
        document.body.style.cursor = 'default';
        if (this.sortingBy === 'created' || this.sortingBy === 'modified') {
          const datesorted = resfiltered.sort((a, b) => new Date(b[this.sortingBy]) - new Date(a[this.sortingBy]));
          console.log(`filter compute: ${(new Date() - startd) / 1000}`);
          return this.sortDir === -1 ? datesorted.slice(0, this.displen) : datesorted.reverse().slice(0, this.displen);
        }
        console.log(`filter compute: ${(new Date() - startd) / 1000}`);
        return resfiltered.sort((a, b) => ((a[this.sortingBy].toLowerCase() > b[this.sortingBy].toLowerCase()) ? this.sortDir : -1 * this.sortDir)).slice(0, this.displen);
      }
      return [];
    },
  },
  mounted() {
    const startd = new Date();
    this.resloaded = this.resources.length > 0;
    this.countAuthors = this.filterBuilder(this.resources, 'author');
    // Object.keys(this.countAuthors).forEach(item => this.authorFilter.push(item));
    this.countOwners = this.filterBuilder(this.resources, 'owner');
    // Object.keys(this.countOwners).forEach(item => this.ownerFilter.push(item));
    this.countContributors = this.filterBuilder(this.resources, 'contributor');
    // Object.keys(this.countContributors).forEach(item => this.contributorFilter.push(item));
    this.countTypes = this.filterBuilder(this.resources, 'type');
    // Object.keys(this.countTypes).forEach(item => this.typeFilter.push(item));

    let subjectbox = [];
    // res.subject is python list js array
    this.resources.forEach((res) => {
      subjectbox = subjectbox.concat(this.enumMulti(res.subject));
    });
    this.countSubjects = new this.Counter(subjectbox);
    // Object.keys(this.countSubjects).forEach(subject => this.subjectFilter
    //   .push(subject));

    let availabilitybox = [];
    // res.availability is python list js array
    this.resources.forEach((res) => {
      availabilitybox = availabilitybox.concat(this.enumMulti(res.availability));
    });
    this.countAvailabilities = new this.Counter(availabilitybox);
    // Object.keys(this.countAvailabilities).forEach(availability => this.availabilityFilter
    //   .push(availability));
    console.log(`mount filter build: ${(new Date() - startd) / 1000}`);
  },
  methods: {
    filterBuilder(resources, thing) {
      const box = [];
      try {
        resources.forEach(res => box.push(res[thing]));
      } catch (err) {
        console.log(`Type ${thing} not found when building filter: ${err}`);
      }
      return new this.Counter(box);
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
        return input.length > 200 ? `${input.substring(0, 200)}...` : input;
      }
      return '';
    },
    displayMap() {
      toggleMap();
    },
    setAllMarkers() {
      deleteMarkers();
      console.log(`num filtered res: ${this.filteredResources.length}`);
      const shids = this.filteredResources.map(x => x.short_id);
      const geopoints = this.geodata.filter(element => shids.indexOf(element.short_id) > -1);
      this.renderMap(geopoints);
    },
    renderMapSingle(pts) {
      pts.forEach((pt) => {
        if (pt.coverage_type === 'point') {
          createMarker({ lat: pt.north, lng: pt.east }, pt.title);
        } else if (pt.coverage_type === 'box') {
          const lat = (parseInt(pt.northlimit, 10) + parseInt(pt.southlimit, 10)) / 2;
          const lng = (parseInt(pt.eastlimit, 10) + parseInt(pt.westlimit, 10)) / 2;
          console.log(pt.northlimit, pt.southlimit, pt.eastlimit, pt.westlimit);
          createMarker({ lat: lat, lng: lng }, pt.title);
        }
      });
    },
    renderMap(geos) {
      console.log(`rendering map: ${geos.length} points`);
      const pts = geos.filter(x => x.coverage_type === 'point');
      const pointlocs = pts.map(x => Object.assign({ lat: x.north, lng: x.east }), {});
      const pointlbls = pts.map(x => x.title);
      createBatchMarkers(pointlocs, pointlbls);
    },
  },
};
</script>

<style scoped>
    #filter-items {
        width: 253px;
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
