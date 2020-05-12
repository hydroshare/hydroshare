<template>
    <div>
<!--        {#        <p class="items-counter">#}-->
<!--        {#        {{ numItems }} items#}-->
<!--        {#        </p>#}-->
        <p v-if="filteredResources.length">Results: {{filteredResources.length}}</p> // TODO redo delimiter to be django friendly
        <div class="table-wrapper">
            <table v-if="filteredResources.length" class="table-hover table-striped resource-custom-table" id="items-discovered">
                <thead>
                <tr>
                    <th v-for="key in labels"
                        @click="sortBy(key)"
                        :class="{ active: sortKey == key }">
                        {{key}}
                        <span class="arrow" :class="sortOrders[key] > 0 ? 'asc' : 'dsc'"></span>
                    </th>
                </tr>
                </thead>
                <tbody>
                <tr v-for="entry in filteredResources">
                    <td>
                        <span>
                            <img v-bind:src="{{ STATIC_URL }} + 'resource-icons/' + resTypeDict[entry.type] + '48x48.png'"
                                 data-toggle="tooltip" data-placement="right"
                                 :alt="entry.type" :title="entry.type"
                                 class="table-res-type-icon"/>
                        </span>

                        <img v-if="entry.availability.indexOf('published') >= 0"
                             src="{{ STATIC_URL }}img/published.png"
                             data-toggle="tooltip" data-placement="right"
                             alt="Published Resource" title="Published"/>
                        <img v-else-if="entry.availability.indexOf('public') >= 0"
                             src="{{ STATIC_URL }}img/public.png"
                             data-toggle="tooltip" data-placement="right"
                             alt="Public Resource" title="Public"/>
                        <img v-else-if="entry.availability.indexOf('discoverable') >= 0"
                             src="{{ STATIC_URL }}img/discoverable.png"
                             data-toggle="tooltip" data-placement="right"
                             alt="Discoverable Resource" title="Discoverable"/>
                        <img v-else="entry.availability.indexOf('private') >= 0"
                             src="{{ STATIC_URL }}img/private.png"
                             data-toggle="tooltip" data-placement="right"
                             alt="Private Resource" title="Private"/>

<!--{#                                    TODO: translate this django template logic into Vue#}-->
<!--{#                                        {% if resource.raccess.published %}#}-->
<!--{#                                            {% if "pending" in cm.doi or "failure" in cm.doi %}#}-->
<!--{#                                                <img src="{{ STATIC_URL }}img/pending.png" alt="Pending Publication"#}-->
<!--{#                                                     data-toggle="tooltip" data-placement="right"#}-->
<!--{#                                                     title="Pending Publication. Note that the DOI will not be available until it has been registered and activated."/>#}-->
<!--{#                                            {% endif %}#}-->
<!--{#                                        {% else %}#}-->
<!--{#                                            {% if resource.raccess.shareable %}#}-->
<!--{#                                                <img src="{{ STATIC_URL }}img/shareable.png" alt="Sharable Resource"#}-->
<!--{#                                                     data-toggle="tooltip" data-placement="right" title="Shareable"/>#}-->
<!--{#                                            {% else %}#}-->
<!--{#                                                <img src="{{ STATIC_URL }}img/non-shareable.png"#}-->
<!--{#                                                     alt="Non Sharable Resource"#}-->
<!--{#                                                     data-toggle="tooltip" data-placement="right"#}-->
<!--{#                                                     title="Not Shareable"/>#}-->
<!--{#                                            {% endif %}#}-->
<!--{#                                        {% endif %}#}-->
                    </td>
                    <td>
                        <a :href="entry.link" data-toggle="tooltip" :title="entry.abstract" data-placement="top">{{entry.name}}</a>
                    </td>
                    <!-- temporary placeholder for link column, until header display approach is refactored -->
                    <td>
                        <a :href="entry.author_link">{{entry.author}}</a>
                    </td>

                    <!-- temporary placeholder for link column, until header display approach is refactored -->
                    <td>{{entry.created}}</td>
                    <td>{{entry.modified}</td>
                </tr>
                </tbody>
            </table>
            <p v-else>No results found.</p>
        </div>
    </div>
</template>

<script>
    export default {
        name: "Resources",
    // delimiters: ['${', '}'],
        props:
            ['sample', 'itemcount', 'columns', 'labels', 'resources', 'filterKey'],
        data: function () {
            this.itemcount ? this.numItems = this.itemcount : this.numItems = 0;
            let sortOrders = {};
            this.columns.forEach(function (key) {
              sortOrders[key] = 1
            });
            return {
                sortKey: '',
                resTypeDict: {
                    // TODO: Expand this dictionary with the rest of the resource types
                    "Composite Resource": "composite",
                    "Generic": "generic",
                    "Geopgraphic Raster": "geographicraster",
                    "Model Program Resource": "modelprogram",
                    "Collection Resource": "collection",
                    "Web App Resource": "webapp",
                    "Time Series": "timeseries",
                    "Model Instance Resource": "modelinstance",
                    "SWAT Model Instance Resource": "swat",
                    "MODFLOW Model Instance Resource": "modflow",
                    "Multidimensional (NetCDF)": "multidimensional"

                },
                sortOrders: sortOrders
            }
        },
        computed: {
            filteredResources: function () {
                let vue = this;
                let sortKey = this.sortKey;
                // let filterKey = this.filterKey && this.filterKey.toLowerCase();
                let order = this.sortOrders[sortKey] || 1;
                let resources = JSON.parse(this.sample);  // TODO validation, security, error handling
                // if (filterKey) {
                //     resources = resources.filter(function (row) {
                //         return Object.keys(row).some(function (key) {
                //             return String(row[key]).toLowerCase().indexOf(filterKey) > -1
                //         })
                //     })
                // }
                if (sortKey) {
                    resources = resources.slice().sort(function (a, b) {
                        a = a[sortKey];
                        b = b[sortKey];
                        return (a === b ? 0 : a > b ? 1 : -1) * order
                    })
                }

                console.log(resources);

                // Vue.set('numItems', 2);
                vue.numItems = resources.length;
                return resources
            },
        },
        filters: {
            capitalize: function (str) {
                if (str !== "link" && str !== "author_link") {  // TODO instead of iterating through headings, explicitly choose and display
                    return str.charAt(0).toUpperCase() + str.slice(1)
                }
            },
            date: function (date) {
                return date;
            }
        },
        methods: {
            sortBy: function (key) {
                this.sortKey = key;
                this.sortOrders[key] = this.sortOrders[key] * -1
            }
        }
    }
</script>

<style scoped>

</style>