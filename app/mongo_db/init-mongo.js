const dbName = process.env.MONGO_INITDB_DATABASE;
const collection_pdq = process.env.MONGO_COLLECTION_PORTAL_DA_QUEIXA;
const collection_pdq_report = process.env.MONGO_COLLECTION_PORTAL_DA_QUEIXA_REPORTS;
const collection_qual_chat = process.env.MONGO_COLLECTION_QUALTRICS_CHATBOT;
const collection_qual_chat_report = process.env.MONGO_COLLECTION_QUALTRICS_CHATBOT_REPORTS;
const collection_cliente_mis = process.env.MONGO_COLLECTION_CLIENTE_MISTERIO;
const collection_cliente_mis_report = process.env.MONGO_COLLECTION_CLIENTE_MISTERIO_REPORTS;
const rootUsername = process.env.MONGO_INITDB_ROOT_USERNAME;
const rootPassword = process.env.MONGO_INITDB_ROOT_PASSWORD;
const newUserUsername = process.env.MONGO_PRINCIPAL_USER;
const newUserPassword = process.env.MONGO_PRINCIPAL_PASSWORD;

db = connect(`mongodb://${rootUsername}:${rootPassword}@localhost:27017/admin`);

db = db.getSiblingDB(dbName); // Create or switch to the specified database

db.createCollection(collection_pdq); // Create the specified collection

db.createCollection(collection_pdq_report);

// db.createCollection(collection_qual_on);

// db.createCollection(collection_qual_on_report);

// Create a new user with read and write permissions
db.createUser({
  user: newUserUsername,
  pwd: newUserPassword,
  roles: [{ role: "readWrite", db: dbName }]
});

