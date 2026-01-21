// Load the file content
const fs = require('fs');
const indexDefinition = JSON.parse(fs.readFileSync("/hs_discover/search_indexes/fuzzy_search.json", "utf8"));

// Connect to the desired database and collection
const dbName = "hydroshare";
const collName = "discovery";

// Create the search index
try {
    db.getSiblingDB(dbName).createCollection(collName, {});
    const result = db.getSiblingDB(dbName).getCollection(collName).createSearchIndex({
        name: "fuzzy_search",
        definition: indexDefinition
    });
    print("Index creation result:", result);
} catch (e) {
    print("Error creating index:", e);
}