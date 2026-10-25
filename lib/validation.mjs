export const SERVICES = Object.freeze([
  'Painting and Decorating', 'Gloss Work and Wood Finishing', 'Property Improvements',
  'Jet Washing', 'One-off House MOT', 'Ongoing Property Maintenance', 'Other / Not Sure'
]);
export const LIMITS = Object.freeze({name: 100, email: 254, phone: 30, service: 80, description: 3000, postcode: 12, timeframe: 100, details: 3000});

export function validateEnquiry(input) {
  const data = {}, errors = {};
  for (const [field, limit] of Object.entries(LIMITS)) {
    if (input[field] != null && typeof input[field] !== 'string') {
      errors[field] = 'Enter text for this field.';
      data[field] = '';
      continue;
    }
    data[field] = (input[field] || '').trim().replace(/\r\n?/g, '\n');
    if (data[field].length > limit) errors[field] = `Use no more than ${limit} characters.`;
    if (/[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/.test(data[field])) errors[field] = 'Remove unsupported control characters.';
    if (!['description', 'details'].includes(field) && /[\r\n]/.test(data[field])) errors[field] = 'Use a single line for this field.';
  }
  if (!data.name) errors.name = 'Enter your full name.';
  if (!data.email && !data.phone) {
    errors.email = 'Provide an email address or telephone number.';
    errors.phone = 'Provide a telephone number or email address.';
  }
  if (data.email && !/^[^\s<>@]+@[^\s<>@]+\.[^\s<>@]+$/.test(data.email)) errors.email = 'Enter a valid email address.';
  if (data.phone && (!/^[+\d\s().-]+$/.test(data.phone) || data.phone.replace(/\D/g, '').length < 7 || data.phone.replace(/\D/g, '').length > 15)) errors.phone = 'Enter a valid telephone number with 7 to 15 digits.';
  if (!SERVICES.includes(data.service)) errors.service = 'Choose a service from the list.';
  if (!data.description) errors.description = 'Describe the work you need.';
  return {data, errors, valid: Object.keys(errors).length === 0};
}
