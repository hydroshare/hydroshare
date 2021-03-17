$(document)
  .ready(function () {
    let PublicationsVm = new Vue({
      el: '#publications-app',
      data: {
        message: "hello world",
        columns: ['name', 'author', 'created', 'modified'],
        filterTo: [],
        groupIds: [],
        groups: [{
          'id': 1,
          'name': 'CZO Sierra',
          'res_count': 1
        }],
        labels: ['Title', 'First Author', 'Date Created', 'Last Modified'],
        pnum: 1,
        pagenum: 1, // initial page number to show
        pagedisp: 1, // page being displayed
        perpage: 0,
        pagecount: 0,
        resources: [],
        rescount: 0,
        resIconName: {
          'Composite Resource': '/static/img/resource-icons/composite48x48.png',
          Generic: '/static/img/resource-icons/generic48x48.png',
          'Geopgraphic Raster': '/static/img/resource-icons/geographicraster48x48.png',
          'Model Program Resource': '/static/img/resource-icons/modelprogram48x48.png',
          'Collection Resource': '/static/img/resource-icons/collection48x48.png',
          'Web App Resource': '/static/img/resource-icons/webapp48x48.png',
          'Time Series': '/static/img/resource-icons/timeseries48x48.png',
          'Script Resource': '/static/img/resource-icons/script48x48.png',
          'Model Instance Resource': '/static/img/resource-icons/modelinstance48x48.png',
          'SWAT Model Instance Resource': '/static/img/resource-icons/swat48x48.png',
          'MODFLOW Model Instance Resource': '/static/img/resource-icons/modflow48x48.png',
          'Multidimensional (NetCDF)': '/static/img/resource-icons/multidimensional48x48.png',
          'HIS Referenced Time Series': '/static/img/resource-icons/his48x48.png',
        },
        sharedByFilter: '',
        sortingBy: 'modified',
        sortDir: -1,
        searchtext: '',
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
      },
      mounted: function () {
        console.log("hello")
        this.searchClick();
        let groupIds = {};

        $('#groups-list li')
          .each(function () {
            let groupId = parseInt($(this)
              .attr('id'));
            groupIds[$(this)
              .text()] = groupId;
          });
        this.$data.groupIds = groupIds;

        let filterGroup = $('#filter-querystring')
          .text();
        if (filterGroup && this.$data.groupIds[filterGroup]) {
          this.$data.filterTo.push(this.$data.groupIds[filterGroup]);
        }
      },
      methods: {
        isVisible(groupId) {
          if (this.$data.filterTo.length === 0) {  // If no selections show all
            return true;
          } else {  // Display row if Group ID found in the filterTo Array
            return this.$data.filterTo.indexOf(groupId) > -1;
          }
        },
        clearSearch() {
          this.searchtext = '';
          this.searchClick(false, true, true);
        },
        paging(direction) {
          let pagecalc = Math.max(1, this.pagenum + Number.parseInt(direction, 10));
          this.pagenum = Math.min(this.pagecount, pagecalc);
          this.searchClick(true);
        },
        updateContribs(groupId) {
          let loc = this.$data.filterTo.indexOf(groupId);

          if (loc < 0) {
            this.$data.filterTo.push(groupId);
          } else {
            this.$data.filterTo.splice(loc, 1);
          }
        },
        ellip(input, size) {
          if (input && size) {
            return input.length > size ? `${input.substring(0, size)}...` : input;
          }
          return '';
        },
        nameList(names) {
          try {
            return names.join(' | ');
          } catch {
            return names;
          }
        },
        sortBy(key) {
          if (this.sortMap[key] !== 'type') {
            this.sortDir = this.sortMap[key] === this.sortingBy ? this.sortDir * -1 : 1;
            this.sortingBy = this.sortMap[key];
            this.searchClick(true);
          }
        },

        sortStyling(key) {
          if (this.sortMap[key] === this.sortingBy) {
            return this.sortDir === 1 ? 'fa fa-fw fa-sort-asc interactive' : 'fa fa-fw fa-sort-desc interactive';
          }
          return this.sortMap[key] === 'type' ? '' : 'fa fa-fw fa-sort interactive';
        },
        searchClick(paging, dofilters, reset) { // paging flag to skip the page reset after data retrieval
          document.body.style.cursor = 'wait';
          axios.get('/discoverapi/', {
            params: {
              q: this.searchtext,
              sort: this.sortingBy,
              asc: this.sortDir,
              pnum: this.pagenum,
            },
          })
            .then((response) => {
              if (response) {
                try {
                  this.resources = JSON.parse(response.data.resources);
                  if (paging !== true) {
                    this.pagenum = 1;
                  }
                  this.pagecount = response.data.pagecount;
                  this.rescount = response.data.rescount;
                  this.perpage = response.data.perpage;
                  this.pagedisp = this.pagenum;
                  document.body.style.cursor = 'default';
                } catch (e) {
                  document.body.style.cursor = 'default';
                }
              }
            })
            .catch((error) => { // eslint-disable-line
              document.body.style.cursor = 'default';
            });
        },
      }
    });
  });
