import {test} from 'node:test';import assert from 'node:assert/strict';import {describeFailure} from './errors';
test('failure categories distinguish cancellation, network and actual provider rejection without raw details',()=>{
 assert.equal(describeFailure('model_under_repair').title,'Model connection under repair');assert.equal(describeFailure('cancelled').title,'Response stopped');assert.equal(describeFailure('network').title,'Connection interrupted');
 const provider=describeFailure('provider_error','Gemma provider returned HTTP 400: secret request detail');assert.equal(provider.title,'Model service error');assert.match(provider.message,/HTTP 400/);assert.doesNotMatch(provider.message,/secret/);
 assert.equal(describeFailure('run_failed','Gemma provider returned HTTP 400').code,'provider_error');assert.match(describeFailure('provider_error','Gemma provider returned HTTP 400: API key expired. Please renew.').message,/expired API key/);
 assert.equal(describeFailure('provider_rate_limited').title,'Model is busy');assert.equal(describeFailure('invalid_model_schema').title,'Answer could not be verified');
});
