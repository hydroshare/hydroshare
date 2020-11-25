<template>
  <div>
    <h2>Resource Name</h2>
    <h3>Abstract</h3>
    <label for="id_abstract"></label><textarea id="id_abstract" class="form-control input-sm textarea" cols="40" rows="10"></textarea>
    <h3>Subject Keywords</h3>
    <h3>Coverage</h3>
      <div id="common-components">
        <!-- https://vuejs.org/v2/guide/components-custom-events.html#Binding-Native-Events-to-Components-->
        <manage-access v-bind:resource.sync="res"></manage-access>
      </div>
    <h3>Content</h3>
      <div id="file-manager">
        <!-- TODO key is probably what resets data reactive reload-->
        <file-manager :key="1234"
                      :sample_prop="sample_props">
        </file-manager>
      </div>
    <h3>Additional Metadata</h3>
    <h3>References</h3>
    <h3>Credits</h3>
    <h3>How to Cite</h3>
    <h3>Comments</h3>
  </div>
</template>

<script>
// import DatePick from 'vue-date-pick';
import 'bootstrap/dist/css/bootstrap.css';
import 'bootstrap-vue/dist/bootstrap-vue.css';
import 'vue-date-pick/dist/vueDatePick.css';
// import axios from 'axios';
import Filemanager from './Filemanager.vue';
import Access from './Access.vue';

export default {
  name: 'Resource',
  data() {
    return {
      resource: {},
      sample_props: ['prop1', 'prop2'],
    };
  },
  components: {
    fileManager: Filemanager,
    manageAccess: Access,
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
