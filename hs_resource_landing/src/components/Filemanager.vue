<template>
  <div>
    Hello Resources
    {{ somedata }}
  </div>
</template>

<script>


export default {
  data() {
    return {
      somedata: 'some sample data',
    };
  },
  name: 'Filemanager',
  props:
  ['sample_prop'],
  components: {
  },
  computed: {
  },
  watch: {

  },
  mounted() {
    // eslint-disable-next-line
    console.log('mounted filemanager');
  },
  methods: {
  },
};
</script>

<style scoped>
    @import url("https://maxcdn.bootstrapcdn.com/font-awesome/4.5.0/css/font-awesome.min.css");

    .btn.focus {
        /* Remove unwanted outline behavior */
        outline: 0;
        box-shadow: None;
    }
    .btn:focus {
        /* Remove unwanted outline behavior */
        outline: 0;
        box-shadow: None;
    }

    .interactive:hover {
      color: LightBlue;
      /* Avoid double-click selection during rapid clicking: */
      user-select: none; /* standard syntax */
      -webkit-user-select: none; /* webkit (safari, chrome) browsers */
      -moz-user-select: none; /* mozilla browsers */
      -ms-user-select: none; /* IE10+ */
    }
</style>
