<template>
    <div id="resources-main">
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
        </div>
        <div id="resource-rows">
            <p v-if="filteredResources.length">Results: {{filteredResources.length}}</p>
            <div class="table-wrapper">
                <table v-if="filteredResources.length"
                       class="table-hover table-striped resource-custom-table" id="items-discovered">
                    <thead>
                    <tr>
                        <th v-for="key in labels" v-bind:key="key"
                            @click="sortBy(key)">
                            <i :class="sortStyling"></i>{{key}}
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
      sortingBy: {},
      sortStyling: 'fa fa-fw fa-sort-asc',
    };
  },
  name: 'Resources',
  props:
  ['resources', 'columns', 'labels'],
  computed: {
    filteredResources() {
      // Filters should be most restrictive when two conflicting states are selected
      const resAuthors = this.resources.filter(element => this.authorFilter.indexOf(element.author) > -1);
      const resSubjects = resAuthors.filter(res => res.subject.filter(val => this.subjectFilter.includes(val)).length > 0);
      const sortDir = Object.keys(this.sortingBy).includes('asc') ? -1 : 1;
      return resSubjects.sort((a, b) => ((a.Title > b.Title) ? sortDir : -1 * sortDir));
    },
  },
  mounted() {
    // eslint-disable-next-line no-return-assign
    this.labels.forEach(x => this.sortingBy[x] = x === 'Title' ? 'fa fa-fw fa-sort-asc' : 'fa fa-fw fa-sort');
    const authorbox = [];
    this.resources.forEach(res => authorbox.push(res.author));
    this.countAuthors = new this.Counter(authorbox);
    Object.keys(this.countAuthors).forEach(author => this.authorFilter
      .push(author)); // populate checkboxes

    const subjectbox = [];
    this.resources.forEach(res => subjectbox.push(res.subject));
    this.countSubjects = new this.Counter(subjectbox);
    Object.keys(this.countSubjects).forEach(subject => this.subjectFilter
      .push(subject)); // populate checkboxes
  },
  methods: {
    sortBy(key) {
      const sortDir = Object.values(this.sortingBy).includes('fa fa-fw fa-sort-asc') ? 'fa fa-fw fa-sort-desc' : 'fa fa-fw fa-sort-asc';
      console.log(key);
      console.log(sortDir);
      this.sortStyling = sortDir;
      // eslint-disable-next-line no-return-assign
      this.labels.forEach(x => this.sortingBy[x] = x === key ? sortDir : 'fa fa-fw fa-sort');
    },
    Counter(array) {
      // eslint-disable-next-line no-return-assign
      array.forEach(val => this[val] = (this[val] || 0) + 1);
    },
  },
};
</script>

<style scoped>
  #resources-main {
    width: 800px;
  }
  #filter-items {
    float: left;
  }
  #resource-rows {
    float: right;
  }
</style>
