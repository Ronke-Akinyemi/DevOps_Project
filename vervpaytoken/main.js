require("dotenv").config();
const express = require("express");
const bodyParser = require("body-parser");
const CryptoJS = require("crypto-js");

const app = express();
app.use(bodyParser.json());

// Load the encryption key from environment variables
const ENCRYPTION_KEY = process.env.VELVE_ENCRYPTION_KEY;
const SECRET_KEY = process.env.VELVE_PRIVATE_KEY;
const PUBLIC_KEY = process.env.VELVE_PUBLIC_KEY;

if (!ENCRYPTION_KEY || !SECRET_KEY || !PUBLIC_KEY) {
    console.error("Error: ENCRYPTION_KEY environment variable is not set.");
    process.exit(1); // Exit if the key is not provided
}

// Encryption endpoint
app.get("/", (req, res) => {
    var REFERENCE_ID = "FR-"+new Date().getTime(); 
    var AUTHORIZATION = SECRET_KEY+PUBLIC_KEY+REFERENCE_ID
    var AUTHORIZATION_TOKEN = CryptoJS.AES.encrypt(AUTHORIZATION,ENCRYPTION_KEY).toString();
    res.send({ token: AUTHORIZATION_TOKEN, refrence_id: REFERENCE_ID });
});

// Start the server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Encryption service running on port ${PORT}`));
