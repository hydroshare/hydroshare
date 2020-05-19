<template>
    <div>
        {{ message }}<br/>
    </div>
</template>

<script>
    export default {
        data() {
            return {
                message: 'Hello world',
            }
        },
        name: "Ping",
        props:
            ['sample'],
        filters: {
            sampleFilter: function (str) {
                }
        },
        methods: {
            sampleMethod: function (key) {
            }
        }
    }
</script>

<style scoped>

</style>
