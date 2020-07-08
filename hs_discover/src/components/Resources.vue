<template>
    <div id="resources-main" class="row">
        <div class="col-xs-12" id="resultsdisp">
            Results: {{filteredResources.length}}
        </div>
        <div class="col-sm-3 col-xs-12" id="facets">
            <div id="filter-items">
                <!-- filter by temporal overlap -->
                <div id="faceting-temporal">
                    <div class="panel panel-default">
                        <div class="panel-heading">
                            <h4 class="panel-title">Temporal</h4>
                        </div>
                        <div v-if="filteredResources.length" id="dateselectors">
                            <date-pick
                                    v-model="startdate"
                                    @change="temporalFilter"
                                    :displayFormat="'MM/DD/YYYY'"
                            ></date-pick>
                            <date-pick
                                    v-model="enddate"
                                    @change="temporalFilter"
                                    :displayFormat="'MM/DD/YYYY'"
                            ></date-pick>
                        </div>
                    </div>
                </div>

                <div id="faceting-creator">
                    <div class="panel panel-default">
                        <div class="panel-heading">
                            <h4 class="panel-title">Filter by author</h4>
                        </div>
                        <div id="creator" class="facet-list panel-collapse collapse in">
                            <ul class="list-group" id="list-group-creator">
                                <li class="list-group-item" v-for="(author) in Object.keys(countAuthors)"
                                    v-bind:key="author">
                                    <span class="badge">{{countAuthors[author]}}</span><label class="checkbox noselect" :for="'author-'+author">{{author}}
                                    <input type="checkbox" class="faceted-selections" :value=author
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
                            <h4 class="panel-title">Filter by owner</h4>
                        </div>
                        <div id="owner" class="facet-list panel-collapse collapse in">
                            <ul class="list-group" id="list-group-owner">
                                <li class="list-group-item" v-for="(owner) in Object.keys(countOwners)"
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
                            <h4 class="panel-title">Filter by subject</h4>
                        </div>
                        <div id="subject" class="facet-list panel-collapse collapse in">
                            <ul class="list-group" id="list-group-subject">
                                <li class="list-group-item" v-for="(subject) in Object.keys(countSubjects)"
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
                            <h4 class="panel-title">Filter by contributor</h4>
                        </div>
                        <div id="contributor" class="facet-list panel-collapse collapse in">
                            <ul class="list-group" id="list-group-contributor">
                                <li class="list-group-item" v-for="(contributor) in Object.keys(countContributors)"
                                    v-bind:key="contributor">
                                    <span class="badge">{{countContributors[contributor]}}</span>
                                    <label class="checkbox noselect" :for="'contrib-'+contributor">{{contributor}}
                                        <input type="checkbox" class="faceted-selections" :value=contributor
                                               v-model="contributorFilter"
                                               :id="'contrib-'+contributor">
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
                            <h4 class="panel-title">Filter by type</h4>
                        </div>
                        <div id="type" class="facet-list panel-collapse collapse in">
                            <ul class="list-group" id="list-group-type">
                                <li class="list-group-item" v-for="(type) in Object.keys(countTypes)"
                                    v-bind:key="type">
                                    <span class="badge">{{countTypes[type]}}</span>
                                    <label class="checkbox noselect" :for="'type-'+type">{{type}}
                                        <input type="checkbox" class="faceted-selections" :value=type
                                               v-model="typeFilter"
                                               :id="'type-'+type">
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
                            <h4 class="panel-title">Filter by availability</h4>
                        </div>
                        <div id="availability" class="facet-list panel-collapse collapse in">
                            <ul class="list-group" id="list-group-availability">
                                <li class="list-group-item" v-for="(availability) in Object.keys(countAvailabilities)"
                                    v-bind:key="availability">
                                    <span class="badge">{{countAvailabilities[availability]}}</span>
                                    <label class="checkbox noselect" :for="'avail-'+availability">{{availability}}
                                        <input type="checkbox" class="faceted-selections" :value=availability
                                               v-model="availabilityFilter"
                                               :id="'avail-'+availability">
                                    </label>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
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
                            <img v-if="entry.shareable" src="/static/img/shareable.png" alt="Sharable Resource"
                                data-toggle="tooltip" data-placement="right" title=""
                                data-original-title="Shareable">
                        </td>
                        <td>
                            <a :href="entry.link" data-toggle="tooltip"
                               :title="entry.abstract" data-placement="top">{{entry.title}}</a>
                        </td>
                        <td>
                            <a :href="entry.author_link">{{entry.author}}</a>
                        </td>
                        <td>{{new Date(entry.created).toDateString()}}</td>
                        <td>{{new Date(entry.modified).toDateString()}}</td>
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

export default {
  data() {
    return {
      startdate: '2019-01-01',
      enddate: '2019-01-01',
      resloaded: false,
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
  ['resources', 'columns', 'labels'],
  components: {
    datePick: DatePick,
  },
  computed: {
    filteredResources() {
      if (this.resloaded) {
        console.log(`filtered resources with length ${this.resources.length}`);
        // Filters should be most restrictive when two conflicting states are selected
        const resAuthors = this.resources.filter(element => this.authorFilter.indexOf(element.author) > -1);
        const resOwners = resAuthors.filter(element => this.ownerFilter.indexOf(element.owner) > -1);
        const resSubjects = resOwners.filter(res => res.subject.filter(val => this.subjectFilter.includes(val)).length > 0);
        const resAvailabilities = resSubjects.filter(res => res.availability.filter(val => this.availabilityFilter.includes(val)).length > 0);
        const resContributors = resAvailabilities.filter(element => this.contributorFilter.indexOf(element.contributor) > -1);
        const resTypes = resContributors.filter(element => this.typeFilter.indexOf(element.type) > -1);
        if (this.sortingBy === 'created' || this.sortingBy === 'modified') {
          return resTypes.sort((a, b) => ((a[this.sortingBy] > b[this.sortingBy]) ? this.sortDir : -1 * this.sortDir));
        }
        return resTypes.sort((a, b) => ((a[this.sortingBy].toLowerCase() > b[this.sortingBy].toLowerCase()) ? this.sortDir : -1 * this.sortDir));
      }
      return [];
    },
  },
  mounted() {
    this.resloaded = this.resources.length > 0;
    this.countAuthors = this.filterBuilder(this.resources, 'author');
    Object.keys(this.countAuthors).forEach(item => this.authorFilter.push(item));
    this.countOwners = this.filterBuilder(this.resources, 'owner');
    Object.keys(this.countOwners).forEach(item => this.ownerFilter.push(item));
    this.countContributors = this.filterBuilder(this.resources, 'contributor');
    Object.keys(this.countContributors).forEach(item => this.contributorFilter.push(item));
    this.countTypes = this.filterBuilder(this.resources, 'type');
    Object.keys(this.countTypes).forEach(item => this.typeFilter.push(item));

    let subjectbox = [];
    // res.subject is python list js array
    this.resources.forEach((res) => {
      subjectbox = subjectbox.concat(this.enumMulti(res.subject));
    });
    this.countSubjects = new this.Counter(subjectbox);
    Object.keys(this.countSubjects).forEach(subject => this.subjectFilter
      .push(subject));

    let availabilitybox = [];
    // res.availability is python list js array
    this.resources.forEach((res) => {
      availabilitybox = availabilitybox.concat(this.enumMulti(res.availability));
    });
    this.countAvailabilities = new this.Counter(availabilitybox);
    Object.keys(this.countAvailabilities).forEach(availability => this.availabilityFilter
      .push(availability));
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
    temporalFilter(ele) {
      console.log(ele);
    },
  },
};
</script>

<style scoped>
    .table-wrapper {
        margin-top: 1px;
    }
    .checkbox {

    }
</style>
