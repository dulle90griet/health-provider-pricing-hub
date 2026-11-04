// Code used early on in the Add Direct Cost form
// Needs to be updated for use in forms with non-required fields
// 
// Generates the comparand in the 'Save' button's 'Update setting Disabled
// to Yes' condition

// Get the object containing all form field values
let formData = $("[Add Direct Cost Form].Value");

// Remove the '_id' field if it exists, as it's a system field that might always be populated
delete formData._id;

// Get an array of all the remaining values
let fieldValues = Object.values(formData);

// Check if any field value is empty, null, or just whitespace
let anyFieldIsEmpty = fieldValues.some(value => {
    return value === null || value === undefined || value.toString().trim() === "";
});

// Return 'true' to disable the button if any field is empty
return anyFieldIsEmpty;