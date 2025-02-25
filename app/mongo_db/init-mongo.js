const dbName = process.env.MONGO_INITDB_DATABASE;
const collectionName = process.env.MONGO_COLLECTION_PORTAL_DA_QUEIXA;
const rootUsername = process.env.MONGO_INITDB_ROOT_USERNAME;
const rootPassword = process.env.MONGO_INITDB_ROOT_PASSWORD;
const newUserUsername = process.env.MONGO_PRINCIPAL_USER;
const newUserPassword = process.env.MONGO_PRINCIPAL_PASSWORD;

db = connect(`mongodb://${rootUsername}:${rootPassword}@localhost:27017/admin`);

db = db.getSiblingDB(dbName); // Create or switch to the specified database

db.createCollection(collectionName); // Create the specified collection

// Create a new user with read and write permissions
db.createUser({
  user: newUserUsername,
  pwd: newUserPassword,
  roles: [{ role: "readWrite", db: dbName }]
});

