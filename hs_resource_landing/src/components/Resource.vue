<template>
  <div>
    <h2>Resource Name</h2>
    <h3>Debug</h3>
    {{res.shortId}}
    {{res.keywords}}
    {{res.resourceAccess}}
    <h3>Abstract</h3>
    <label for="id_abstract"></label><textarea id="id_abstract" class="form-control input-sm textarea" cols="40" rows="10"></textarea>
    <h3>Subject Keywords</h3>
    <h3>Coverage</h3>
      <div id="common-components">
        <!-- https://vuejs.org/v2/guide/components-custom-events.html#Binding-Native-Events-to-Components-->
<!--        <manage-access></manage-access>-->
      </div>
    <h3>Content</h3>
      <div id="file-manager">
        <file-manager v-bind.sync="res"></file-manager>
<!--        <file-manager :key="1234" :sample_prop="sample_props"></file-manager>-->
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
// import Access from './Access.vue';

export default {
  name: 'Resource',
  data() {
    return {
      res: {
        shortId: '7ada0db58127435c97075a9516b4912b',
        keywords: 'diatoms',
        resourceAccess: {
          isPublic: true,
          isDiscoverable: true,
          isShareable: true,
        },
        currentUserId: 'TODO',
        users_json: [{ // TODO RESEARCH WHY THIS IS A LIST
          access: 'owner',
          best_name: 'CZO Sierra',
          can_undo: false,
          contributions: 6,
          country: 'Unspecified',
          email: 'czosier@noreply.org',
          id: 12,
          identifiers: {}, // TODO
          joined: '30 Sep, 2019',
          loading: false,
          organization: 'CZO',
          pictureUrl: null,
          state: 'Unspecified',
          subject_areas: null,
          title: null,
          user_name: 'czo_sierra',
          user_type: 'user',
        }],
      },
      sample_props: ['prop1', 'prop2'],
    };
  },
  watch: {
  },
  components: {
    fileManager: Filemanager,
    // manageAccess: Access,
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
