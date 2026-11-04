// Code generating the unit_price_override_gbp value to send to the server
// when saving a new tender line item - 0 values are converted to 'null'

value = $("[Create Line Item Form].Fields.unit_price_override_gbp");
if (value > 0) {
  return value.toString();
} else {
  return null;
}
