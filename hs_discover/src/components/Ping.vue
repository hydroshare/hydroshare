<template>
    <div>
        {{ message }}
    </div>
</template>

<script>
    export default {
        data() {
            return {
                message: 'Hello world',
            }
        },
        name: "Ping", // delimiters: ['${', '}'],
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
