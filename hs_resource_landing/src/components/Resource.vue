<template>
  <div>
    <h2>Resource Name</h2>
    <h3>Content</h3>
    <h3>Abstract</h3>
      <textarea id="id_abstract" class="form-control input-sm textarea" cols="40" rows="10"></textarea>
    <h3>Subject Keywords</h3>
    <h3>Coverage</h3>
    <h3>Content</h3>
    <h3>Additional Metadata</h3>
    <h3>References</h3>
    <h3>Credits</h3>
    <h3>How to Cite</h3>
    <h3>Comments</h3>
    <div id="file-manager">
        <file-manager :key="data"
                      :sample_prop="sample_props">
        </file-manager>
    </div>
  </div>
</template>

<script>
// import DatePick from 'vue-date-pick';
import 'vue-date-pick/dist/vueDatePick.css';
// import axios from 'axios';
import Filemanager from './Filemanager.vue';

export default {
  name: 'Search',
  data() {
    return {
      data: { first: 'asdf' },
      sample_props: ['prop1', 'prop2'],
    };
  },
  components: {
    fileManager: Filemanager,
  },
  mounted() {
  },
  methods: {
  },
};
</script>

<style scoped>
  h1, h2, h3, h4, h5, h6 {
    font-family: Lato, sans-serif;
  }

  h3 {
    font-size: 24px;
    padding-bottom: 10px;
    margin-top: 40px;
    color: rgb(75, 181, 193);
    border-bottom: 1px solid rgb(238, 238, 238);
  }

</style>
