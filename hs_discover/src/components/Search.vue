<template>
    <div id="discover-search">
        <div id="wrapper">

            <div id="search" class="search-field" @keyup.enter="searchClick('{{ csrf_token }}')">
                <span class="glyphicon glyphicon-search search-icon"></span>
                <span @click="clearSearch()" class="glyphicon glyphicon-remove-sign btn-clear-search c-pointer"></span>
                <input v-model="message" placeholder="Search all Public and Discoverable Resources">
            </div>
        </div>
<!--        <div v-if="q">-->
                        {{ sample_item }}

            <resource-listing :sample="sample"
                              :itemcount="5"
                              :columns="gridColumns"
                              :labels="gridColumnLabels"
                              :filter-key="searchQuery">
            </resource-listing>

<!--                        <resource-listing :sample="{{ resources }}"-->
<!--                              :itemcount="{{ initialitemcount }}"-->
<!--                              :columns="gridColumns"-->
<!--                              :labels="gridColumnLabels"-->
<!--                              :filter-key="searchQuery">-->
<!--            </resource-listing>-->
<!--        </div>-->
    </div>
</template>

<script>
    import Resources from './Resources.vue';
    export default {
        name: "Search",
        data() {
            return {
                csrf_token: 'abc123',
                message: ''
            }
        },
        components: {
            resourceListing: Resources
        }
    };
</script>

<style scoped>
    /*<link rel="stylesheet" type="text/css" href="{{ STATIC_URL }}css/search.css"/>*/
    #wrapper {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        margin-bottom: 2em;
    }

    #wrapper .search-field, #advanced-discover-search {
        flex-grow: 1;
        max-width: 600px;
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

    #items-discovered {
        margin-top: 1em;
    }

    #advanced-search-items {
        margin-top: 1em;
        max-width: 600px;
    }

    table tr th {
        cursor: pointer;
    }

    div.table-wrapper {
        max-width: 100%;
        overflow: auto;
    }

    .btn-clear-search {
        position: absolute;
        top: 10px;
        right: 8px;
    }
</style>
