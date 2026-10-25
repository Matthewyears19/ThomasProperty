import {handleEnquiry} from '../../lib/enquiry.mjs';

export async function onRequest(context) {
  return handleEnquiry(context);
}
