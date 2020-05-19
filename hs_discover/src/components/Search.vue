<template>
                    <div id="discover-search">
                    <div id="wrapper">
                        <div id="search" class="search-field" @keyup.enter="searchClick('{{ csrf_token }}')">
                            <span class="glyphicon glyphicon-search search-icon"></span>
                            <span @click="clearSearch()" class="glyphicon glyphicon-remove-sign btn-clear-search c-pointer"></span>
                        </div>
                        <a href="{% url 'search' %}?mode=advanced">Advanced Search</a>
                    </div>

                    <div v-if="q">
                        <resource-listing sample="{{ resources }}" itemcount="{{ initialitemcount }}"
                                          :columns="gridColumns"
                                          :labels="gridColumnLabels"
                                          :filter-key="searchQuery">
                        </resource-listing>
                    </div>
                </div>
            </div>
        <link rel="stylesheet" type="text/css" href="{{ STATIC_URL }}css/search.css"/>
</template>

<script>
    export default {
        data() {
            return {
                message: 'initial message'
            }
        }
    }
</script>
