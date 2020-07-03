<template>
    <div id="resources-main" class="row">
        <div class="col-sm-3 col-xs-12" id="facets">
            <div id="filter-items">
            <!-- filter by creator -->
            <div id="faceting-creator">
                <div class="panel panel-default">
                    <div class="panel-heading">
                        <h4 class="panel-title">
                            <a data-toggle="collapse" href="#creator">
                                &nbsp; Filter by author
                                <span class="glyphicon glyphicon-minus pull-left">
                            </span>
                            </a>
                        </h4>
                    </div>
                    <div id="creator" class="facet-list panel-collapse collapse in">
                        <ul class="list-group" id="list-group-creator">
                            <li class="list-group-item" v-for="(author) in Object.keys(countAuthors)"
                                v-bind:key="author">
                                <span class="badge">{{countAuthors[author]}}</span>
                                <label class="checkbox noselect" :for="name-author">{{author}}
                                    <input type="checkbox" class="faceted-selections" :value=author
                                         v-model="authorFilter"
                                         :id="name-author">
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
                            <a data-toggle="collapse" href="#owner">
                                &nbsp; Filter by owner
                                <span class="glyphicon glyphicon-minus pull-left">
                            </span>
                            </a>
                        </h4>
                    </div>
                    <div id="owner" class="facet-list panel-collapse collapse in">
                        <ul class="list-group" id="list-group-owner">
                            <li class="list-group-item" v-for="(owner) in Object.keys(countOwners)"
                                v-bind:key="owner">
                                <span class="badge">{{countOwners[owner]}}</span>
                                <label class="checkbox noselect" :for="name-owner">{{owner}}
                                    <input type="checkbox" class="faceted-selections" :value=owner
                                         v-model="ownerFilter"
                                         :id="name-owner">
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
                            <a data-toggle="collapse" href="#subject">
                                &nbsp; Filter by subject
                                <span class="glyphicon glyphicon-minus pull-left">
                            </span>
                            </a>
                        </h4>
                    </div>
                    <div id="subject" class="facet-list panel-collapse collapse in">
                        <ul class="list-group" id="list-group-subject">
                            <li class="list-group-item" v-for="(subject) in Object.keys(countSubjects)"
                                v-bind:key="subject">
                                <span class="badge">{{countSubjects[subject]}}</span>
                                <label class="checkbox noselect" :for="name-subject">{{subject}}
                                    <input type="checkbox" class="faceted-selections" :value=subject
                                         v-model="subjectFilter"
                                         :id="name-subject">
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
                            <a data-toggle="collapse" href="#contributor">
                                &nbsp; Filter by contributor
                                <span class="glyphicon glyphicon-minus pull-left">
                            </span>
                            </a>
                        </h4>
                    </div>
                    <div id="contributor" class="facet-list panel-collapse collapse in">
                        <ul class="list-group" id="list-group-contributor">
                            <li class="list-group-item" v-for="(contributor) in Object.keys(countContributors)"
                                v-bind:key="contributor">
                                <span class="badge">{{countContributors[contributor]}}</span>
                                <label class="checkbox noselect" :for="name-contributor">{{contributor}}
                                    <input type="checkbox" class="faceted-selections" :value=contributor
                                         v-model="contributorFilter"
                                         :id="name-contributor">
                                </label>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>


<!--                    <div id="faceting-content_type">-->
<!--                        <div class="panel panel-default">-->
<!--                            <div class="panel-heading">-->
<!--                                <h4 class="panel-title">-->
<!--                                    <a data-toggle="collapse" href="#content_type">-->
<!--                                        &nbsp; Filter by content type-->
<!--                                        <span class="glyphicon glyphicon-minus pull-left">-->
<!--                                        </span>-->
<!--                                    </a>-->
<!--                                </h4>-->
<!--                            </div>-->

<!--                            <div id="content_type" class="facet-list panel-collapse collapse in">-->
<!--                                <ul class="list-group" id="list-group-content_type">-->
<!--                                    <li class="list-group-item" rel="content_type,Composite">-->
<!--                                        <span class="badge">3911</span>-->
<!--                                        <label class="checkbox noselect">-->
<!--                                            <input type="checkbox" class="faceted-selections"-->
<!--                                                   id="content_type-Composite" value="content_type,Composite">Composite</label>-->
<!--                                    </li>-->
<!--                                    <li class="list-group-item" rel="content_type,Generic Data">-->
<!--                                        <span class="badge">2238</span>-->
<!--                                        <label class="checkbox noselect">-->
<!--                                            <input type="checkbox" class="faceted-selections"-->
<!--                                                   id="content_type-Generic Data" value="content_type,Generic Data">Generic-->
<!--                                            Data</label>-->
<!--                                    </li>-->
<!--                                    <li class="list-group-item" rel="content_type,Geographic Feature (ESRI Shapefiles)">-->
<!--                                        <span class="badge">1132</span>-->
<!--                                        <label class="checkbox noselect">-->
<!--                                            <input type="checkbox" class="faceted-selections"-->
<!--                                                   id="content_type-Geographic Feature (ESRI Shapefiles)"-->
<!--                                                   value="content_type,Geographic Feature (ESRI Shapefiles)">Geographic-->
<!--                                            Feature (ESRI Shapefiles)</label>-->
<!--                                    </li>-->
<!--                                    <li class="list-group-item" rel="content_type,Spreadsheet">-->
<!--                                        <span class="badge">1053</span>-->
<!--                                        <label class="checkbox noselect">-->
<!--                                            <input type="checkbox" class="faceted-selections"-->
<!--                                                   id="content_type-Spreadsheet" value="content_type,Spreadsheet">Spreadsheet</label>-->
<!--                                    </li>-->
<!--                                    <li class="list-group-item" rel="content_type,Document">-->
<!--                                        <span class="badge">672</span>-->
<!--                                        <label class="checkbox noselect">-->
<!--                                            <input type="checkbox" class="faceted-selections" id="content_type-Document"-->
<!--                                                   value="content_type,Document">Document</label>-->
<!--                                    </li>-->
<!--                                    <li class="list-group-item" rel="content_type,Jupyter Notebook">-->
<!--                                        <span class="badge">313</span>-->
<!--                                        <label class="checkbox noselect">-->
<!--                                            <input type="checkbox" class="faceted-selections"-->
<!--                                                   id="content_type-Jupyter Notebook"-->
<!--                                                   value="content_type,Jupyter Notebook">Jupyter Notebook</label>-->
<!--                                    </li>-->
<!--                                    <li class="list-group-item" rel="content_type,Image">-->
<!--                                        <span class="badge">288</span>-->
<!--                                        <label class="checkbox noselect">-->
<!--                                            <input type="checkbox" class="faceted-selections" id="content_type-Image"-->
<!--                                                   value="content_type,Image">Image</label>-->
<!--                                    </li>-->
<!--                                    <li class="list-group-item" rel="content_type,Presentation">-->
<!--                                        <span class="badge">233</span>-->
<!--                                        <label class="checkbox noselect">-->
<!--                                            <input type="checkbox" class="faceted-selections"-->
<!--                                                   id="content_type-Presentation" value="content_type,Presentation">Presentation</label>-->
<!--                                    </li>-->
<!--                                    <li class="list-group-item" rel="content_type,Reference to Time Series">-->
<!--                                        <span class="badge">4</span>-->
<!--                                        <label class="checkbox noselect">-->
<!--                                            <input type="checkbox" class="faceted-selections"-->
<!--                                                   id="content_type-Reference to Time Series"-->
<!--                                                   value="content_type,Reference to Time Series">Reference to Time-->
<!--                                            Series</label>-->
<!--                                    </li>-->
<!--                                </ul>-->
<!--                            </div>-->
<!--                        </div>-->
<!--                    </div>-->


<!--                    <div id="faceting-availability">-->
<!--                        <div class="panel panel-default">-->
<!--                            <div class="panel-heading">-->
<!--                                <h4 class="panel-title">-->
<!--                                    <a data-toggle="collapse" href="#availability">-->
<!--                                        &nbsp; Filter by availability-->
<!--                                        <span class="glyphicon glyphicon-minus pull-left">-->
<!--                                        </span>-->
<!--                                    </a>-->
<!--                                </h4>-->
<!--                            </div>-->

<!--                            <div id="availability" class="facet-list panel-collapse collapse in">-->
<!--                                <ul class="list-group" id="list-group-availability">-->
<!--                                    <li class="list-group-item" rel="availability,public">-->
<!--                                        <span class="badge">3320</span>-->
<!--                                        <label class="checkbox noselect">-->
<!--                                            <input type="checkbox" class="faceted-selections" id="availability-public"-->
<!--                                                   value="availability,public">public</label>-->
<!--                                    </li>-->
<!--                                    <li class="list-group-item" rel="availability,discoverable">-->
<!--                                        <span class="badge">682</span>-->
<!--                                        <label class="checkbox noselect">-->
<!--                                            <input type="checkbox" class="faceted-selections"-->
<!--                                                   id="availability-discoverable" value="availability,discoverable">discoverable</label>-->
<!--                                    </li>-->


<!--                                    <li class="list-group-item" rel="availability,published">-->
<!--                                        <span class="badge">377</span>-->
<!--                                        <label class="checkbox noselect">-->
<!--                                            <input type="checkbox" class="faceted-selections"-->
<!--                                                   id="availability-published" value="availability,published">published</label>-->
<!--                                    </li>-->
<!--                                </ul>-->
<!--                            </div>-->
<!--                        </div>-->
<!--                    </div>-->
            </div>
        </div>
        <div id="resource-rows" class="col-sm-9 col-xs-12">
            <p v-if="filteredResources.length">Results: {{filteredResources.length}}</p>
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
                            <img :src="entry.availabilityurl" data-toggle="tooltip"
                                 :title="entry.availability" :alt="entry.availability" :key="entry">
                        </td>
                        <td>
                            <a :href="entry.link" data-toggle="tooltip"
                               :title="entry.abstract" data-placement="top">{{entry.title}}</a>
                        </td>
                        <td>
                            <a :href="entry.author_link">{{entry.author}}</a>
                        </td>
                        <td>{{entry.created}}</td>
                        <td>{{entry.modified}}</td>
                    </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</template>

<script>
export default {
  data() {
    return {
      countAuthors: {},
      authorFilter: [],
      countSubjects: {},
      subjectFilter: [],
      countOwners: {},
      ownerFilter: [],
      countContributors: {},
      contributorFilter: [],
      sortDir: 1,
      sortingBy: 'Last Modified',
    };
  },
  name: 'Resources',
  props:
  ['resources', 'columns', 'labels'],
  computed: {
    filteredResources() {
      // Filters should be most restrictive when two conflicting states are selected
      const resAuthors = this.resources.filter(element => this.authorFilter.indexOf(element.author) > -1);
      const resOwners = resAuthors.filter(element => this.ownerFilter.indexOf(element.owner) > -1);
      const resSubjects = resOwners.filter(res => res.subject.filter(val => this.subjectFilter.includes(val)).length > 0);
      const resContributors = this.resources.filter(element => this.contributorFilter.indexOf(element.contributor) > -1);
      return resSubjects.sort((a, b) => ((a.Title > b.Title) ? this.sortDir : -1 * this.sortDir));
    },
  },
  mounted() {
    const authorbox = [];
    this.resources.forEach(res => authorbox.push(res.author));
    this.countAuthors = new this.Counter(authorbox);
    Object.keys(this.countAuthors).forEach(author => this.authorFilter
      .push(author));

    const ownerbox = [];
    this.resources.forEach(res => ownerbox.push(res.owner));
    this.countOwners = new this.Counter(ownerbox);
    Object.keys(this.countOwners).forEach(owner => this.ownerFilter
      .push(owner));

    const contributorbox = [];
    this.resources.forEach(res => contributorbox.push(res.contributor));
    this.countContributors = new this.Counter(contributorbox);
    Object.keys(this.countContributors).forEach(contributor => this.contributorFilter
      .push(contributor));

    let subjectbox = [];
    // res.subject is python list js array
    this.resources.forEach((res) => {
      subjectbox = subjectbox.concat(this.enumMulti(res.subject));
    });
    this.countSubjects = new this.Counter(subjectbox);
    Object.keys(this.countSubjects).forEach(subject => this.subjectFilter
      .push(subject));
  },
  methods: {
    sortBy(key) {
      this.sortDir = key === this.sortingBy ? this.sortDir * -1 : this.sortDir;
      this.sortingBy = key;
    },
    sortStyling(key) {
      if (key === this.sortingBy) {
        return this.sortDir === 1 ? 'fa fa-fw fa-sort-asc' : 'fa fa-fw fa-sort-desc';
      }
      return 'fa fa-fw fa-sort';
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
      // console.log(ret)
      return c;
    },
  },
};
</script>

<style scoped>
</style>
