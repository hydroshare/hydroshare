<template>
    <div id="discover-search">
        <resource-listing :key="resources"
                          :columns="gridColumns"
                          :labels="gridColumnLabels">
        </resource-listing>
    </div>
</template>

<script>
import Resources from './Resources.vue';

export default {
  name: 'Search',
  data() {
    return {
      gridColumns: ['name', 'author', 'created', 'modified'],
      gridColumnLabels: ['Title', 'First Author', 'Date Created', 'Last Modified'],
    };
  },
  components: {
    resourceListing: Resources,
  },
  mounted() {
  },
  methods: {
  },
};
</script>
