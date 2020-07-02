<template>
    <div class="main-container">
    <input type="hidden" id="static-url" value="/static/">
    <div class="container" id="discover-main">
        <div class="row">

            <div class="col-sm-3 col-xs-12" id="facets">
<!--                <div>-->
<!--                    <button id="btn-show-all" data-toggle="tooltip" data-placement="right" class="btn btn-default"-->
<!--                            title="Show All Public and Discoverable Resources">Show All-->
<!--                    </button>-->
<!--                </div>-->

<!--                <div id="filter-items">-->


<!--                    <div id="faceting-contributor">-->
<!--                        <div class="panel panel-default">-->
<!--                            <div class="panel-heading">-->
<!--                                <h4 class="panel-title">-->
<!--                                    <a data-toggle="collapse" href="#contributor">-->
<!--                                        &nbsp; Filter by contributor-->
<!--                                        <span class="glyphicon glyphicon-minus pull-left">-->
<!--                                        </span>-->
<!--                                    </a>-->
<!--                                </h4>-->
<!--                            </div>-->

<!--                            <div id="contributor" class="facet-list panel-collapse collapse in">-->
<!--                                <ul class="list-group" id="list-group-contributor">-->
<!--                                    <li class="list-group-item" rel="contributor,Eiriksson, Dave">-->
<!--                                        <span class="badge">65</span>-->
<!--                                        <label class="checkbox noselect">-->
<!--                                            <input type="checkbox" class="faceted-selections"-->
<!--                                                   id="contributor-Eiriksson, Dave" value="contributor,Eiriksson, Dave">Eiriksson,-->
<!--                                            Dave</label>-->
<!--                                    </li>-->
<!--                                    <li class="list-group-item"-->
<!--                                        rel="contributor,Los Angeles County Arboretum and Botanic Garden">-->
<!--                                        <span class="badge">2</span>-->
<!--                                        <label class="checkbox noselect">-->
<!--                                            <input type="checkbox" class="faceted-selections"-->
<!--                                                   id="contributor-Los Angeles County Arboretum and Botanic Garden"-->
<!--                                                   value="contributor,Los Angeles County Arboretum and Botanic Garden">Los-->
<!--                                            Angeles County Arboretum and Botanic Garden</label>-->
<!--                                    </li>-->
<!--                                </ul>-->
<!--                            </div>-->
<!--                        </div>-->
<!--                    </div>-->
<!--                    <div id="faceting-owner">-->
<!--                        <div class="panel panel-default">-->
<!--                            <div class="panel-heading">-->
<!--                                <h4 class="panel-title">-->
<!--                                    <a data-toggle="collapse" href="#owner">-->
<!--                                        &nbsp; Filter by owner-->
<!--                                        <span class="glyphicon glyphicon-minus pull-left">-->
<!--                                        </span>-->
<!--                                    </a>-->
<!--                                </h4>-->
<!--                            </div>-->

<!--                            <div id="owner" class="facet-list panel-collapse collapse in">-->
<!--                                <ul class="list-group" id="list-group-owner">-->
<!--                                    <li class="list-group-item" rel="owner,CZO National">-->
<!--                                        <span class="badge">491</span>-->
<!--                                        <label class="checkbox noselect">-->
<!--                                            <input type="checkbox" class="faceted-selections" id="owner-CZO National"-->
<!--                                                   value="owner,CZO National">CZO National</label>-->
<!--                                    </li>-->
<!--                                    <li class="list-group-item" rel="owner,Christopher, Adrian">-->
<!--                                        <span class="badge">483</span>-->
<!--                                        <label class="checkbox noselect">-->
<!--                                            <input type="checkbox" class="faceted-selections"-->
<!--                                                   id="owner-Christopher, Adrian" value="owner,Christopher, Adrian">Christopher,-->
<!--                                            Adrian</label>-->
<!--                                    </li>-->
<!--                                    <li class="list-group-item" rel="owner,Sheeley, Jason">-->
<!--                                        <span class="badge">483</span>-->
<!--                                        <label class="checkbox noselect">-->
<!--                                            <input type="checkbox" class="faceted-selections" id="owner-Sheeley, Jason"-->
<!--                                                   value="owner,Sheeley, Jason">Sheeley, Jason</label>-->
<!--                                    </li>-->
<!--                                    <li class="list-group-item" rel="owner,Gish, Brian">-->
<!--                                        <span class="badge">304</span>-->
<!--                                        <label class="checkbox noselect">-->
<!--                                            <input type="checkbox" class="faceted-selections" id="owner-Gish, Brian"-->
<!--                                                   value="owner,Gish, Brian">Gish, Brian</label>-->
<!--                                    </li>-->
<!--                                    <li class="list-group-item" rel="owner,Pomeroy, Christine">-->
<!--                                        <span class="badge">7</span>-->
<!--                                        <label class="checkbox noselect">-->
<!--                                            <input type="checkbox" class="faceted-selections"-->
<!--                                                   id="owner-Pomeroy, Christine" value="owner,Pomeroy, Christine">Pomeroy,-->
<!--                                            Christine</label>-->
<!--                                    </li>-->
<!--                                </ul>-->
<!--                            </div>-->
<!--                        </div>-->
<!--                    </div>-->

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
            <div class="col-sm-9 col-xs-12" id="items">
                    <div id="discover-search">
        <div>
            <h2 class="page-title">Discover
                <small class="text-muted"><i>Public resources shared with the community.</i></small>
            </h2>
<!--            <span id="solr-help-info" class="glyphicon-->
<!--            glyphicon-info-sign info-popover-glypn-->
<!--            c-pointer" data-toggle="popover"-->
<!--                  data-placement="bottom" data-original-title="" title="">-->
<!--            </span>-->
            <div id="search" @keyup.enter="searchClick()">
                <!--                <i class="glyphicon glyphicon-search search-icon"></i>-->
                <input type="search" class="form-control" v-model="searchtext"
                       placeholder="Search all Public and Discoverable Resources">
            </div>
        </div>
        <!--        <div class="flex">-->
        <!--            <h2 class="page-title">Discover-->
        <!--                <small class="text-muted"><i>Public resources shared with the community.</i></small>-->
        <!--            </h2>-->
        <!--            <br>-->
        <!--            <div class="flex">-->
        <!--                    <span id="solr-help-info" class="glyphicon glyphicon-info-sign info-popover-glypn c-pointer"-->
        <!--                          data-toggle="popover"-->
        <!--                          data-placement="bottom">-->
        <!--                    </span>-->
        <!--                <div id="discover-resource-search" class="resource-search">-->
        <!--                    <div class="search-field">-->
        <!--                        <span class="glyphicon glyphicon-search search-icon"></span>-->
        <!--                        <input type="search" class="form-control" v-model="searchtext"-->
        <!--                               placeholder="Search all Public and Discoverable Resources">-->
        <!--                    </div>-->
        <!--                    >-->
        <!--                </div>-->
        <!--            </div>-->
        <!--        </div>-->
        <table cellpadding='20'>
            <tr>
                <td>
                    <form id="date-search-fields" method="get" action=".">
                        <h4 class="text-muted">Temporal Coverage</h4>
                        <table>
                            <tr>
                                <td>
                                    <div class="fieldWrapper">
                                        <span class="glyphicon glyphicon-calendar text-muted"></span> <label
                                            for="id_start_date">From Date:</label> <input type="text"
                                                                                          name="start_date"
                                                                                          id="id_start_date"/>
                                    </div>
                                </td>
                                <td>
                                    <div class="fieldWrapper">
                                        <span class="glyphicon glyphicon-calendar text-muted"></span> <label
                                            for="id_end_date">To Date:</label> <input type="text"
                                                                                      name="end_date"
                                                                                      id="id_end_date"/>
                                    </div>
                                </td>
                                <td>
                                    <a id="clear-dates-options" data-toggle="tooltip" title="Clear Dates"
                                       class="glyphicon glyphicon-remove-circle icon-remove"></a>
                                </td>
                            </tr>
                        </table>
                    </form>
                </td>
                <td>
                    &nbsp;
                </td>
            </tr>
        </table>
        <resource-listing :resources="resources"
                          :key="resources"
                          :columns="gridColumns"
                          :labels="gridColumnLabels">
        </resource-listing>
<!--    </div>-->
            </div>
        </div>
    </div>

</div>
</template>

<script>
    import axios from 'axios';
    import Resources from './Resources.vue';

    export default {
        name: 'Search',
        data() {
            return {
                resources: [],
                searchtext: '',
                gridColumns: ['availability', 'name', 'author', 'created', 'modified'],
                gridColumnLabels: ['Availability', 'Title', 'First Author', 'Date Created', 'Last Modified'],
            };
        },
        components: {
            resourceListing: Resources,
        },
        beforeMount() {
        },
        mounted() {
            this.searchClick();
        },
        methods: {
            searchClick() {
                axios.get('/discoverapi/', {params: {searchtext: this.$data.searchtext}})
                    .then((response) => {
                        this.$data.resources = JSON.parse(response.data.resources);
                    })
                    .catch((error) => {
                        console.error(error); // eslint-disable-line
                    });
            },
        },
    };
</script>

<style scoped>
    #wrapper {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        margin-bottom: 2em;
    }

    #wrapper .search-field, #advanced-discover-search {
        flex-grow: 1;
        max-width: 500px;
        position: relative;
    }

    #wrapper .search-field div {
        width: 100%;
    }

    #wrapper > a {
        margin-left: 1em;
    }

    #search input {
        width: 100%;
        padding-left: 25px;
        padding-right: 25px;
    }

    table tr th {
        cursor: pointer;
    }

    div.table-wrapper {
        max-width: 100%;
        overflow: auto;
    }

</style>
