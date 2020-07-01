<template>
      <div id="filter-items">
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
                            <li class="list-group-item" v-for="(author) in Object.keys(countAuthors)" v-bind:key="author">
                                <span class="badge">{{countAuthors[author]}}</span>
                                <label class="checkbox noselect" :for="name-author">{{author}}
                                <input type="checkbox" class="faceted-selections" :value=author v-model="authorFilter" :id="name-author">
                                </label>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>

    <div>
        <p v-if="filteredResources.length">Results: {{filteredResources.length}}</p>
        <div class="table-wrapper">
<!--            <h3 v-if="Object.keys(countAuthors).length">Author Filter</h3>-->
<!--            <div v-for="(author) in Object.keys(countAuthors)" v-bind:key="author">-->
<!--                <input type="checkbox" :value=author v-model="authorFilter" :id="name-author">-->
<!--                <label :for="name-author">{{author}}&nbsp;{{countAuthors[author]}}</label>-->
<!--            </div>-->
            <table v-if="filteredResources.length"
                   class="table-hover table-striped resource-custom-table" id="items-discovered">
                <thead>
                    <tr>
                        <th v-for="key in labels" v-bind:key="key"
                            @click="sortBy(key)"
                            :class="{ active: sortKey === key }">
                            {{key}}
                            <span class="arrow" :class="sortOrders[key] >
                            0 ? 'asc' : 'dsc'"></span>
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
                           :title="entry.abstract" data-placement="top">{{entry.name}}</a>
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
      sortKey: '',
      sortOrders: { Type: -1, Title: 1, 'First Author': -1 },
    };
  },
  name: 'Resources',
  props:
  ['resources', 'columns', 'labels'],
  computed: {
    filteredResources() {
      const { sortKey } = this;
      if (sortKey) {
        // do nothing
      }
      let res = this.resources.filter(element => this.authorFilter.indexOf(element.author) > -1);
      // res = res.filter(element => this.subjectFilter.indexOf(element.subject) > -1);
      return res;
    },
  },
  mounted() {
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
      this.sortKey = key;
      this.sortOrders[key] = this.sortOrders[key] * -1;
    },
    Counter(array) {
      // eslint-disable-next-line no-return-assign
      array.forEach(val => this[val] = (this[val] || 0) + 1);
    },
  },
};
</script>

<style scoped>
    .arrow {
      display: inline-block;
      vertical-align: middle;
      width: 0;
      height: 0;
      margin-left: 5px;
      opacity: 0.66;
    }

    .arrow.asc {
      border-left: 4px solid transparent;
      border-right: 4px solid transparent;
      border-bottom: 4px solid #000000;
    }

    .arrow.dsc {
      border-left: 4px solid transparent;
      border-right: 4px solid transparent;
      border-top: 4px solid #000000;
    }
</style>
