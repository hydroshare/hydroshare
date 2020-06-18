<template>
    <div>
        <p v-if="filteredResources.length">Results: {{filteredResources.length}}</p>
        <div class="table-wrapper">
            <h3 v-if="Object.keys(counters).length">Author Filter</h3>
            <div v-for="(author) in Object.keys(counters)" v-bind:key="author">
                <input type="checkbox" :value=author v-model="authorFilter" :id="name-author">
                <label :for="name-author">{{author}}&nbsp;{{counters[author]}}</label>
            </div>
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
</template>

<script>
export default {
  data() {
    return {
      counters: {},
      authorFilter: [],
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
      return this.resources.filter(element => this.authorFilter.indexOf(element.author) > -1);
    },
  },
  mounted() {
    const authorbox = [];
    this.resources.forEach(res => authorbox.push(res.author));
    // console.log(new this.Counter(authorbox)); // eslint-disable-line
    this.counters = new this.Counter(authorbox);
    Object.keys(this.counters).forEach(author => this.authorFilter
      .push(author)); // populate checkboxes
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
