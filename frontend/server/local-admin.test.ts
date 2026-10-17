import {test} from 'node:test';import assert from 'node:assert/strict';import {allowedAdminPath,localOrigin} from './local-admin';
test('local diagnostic capability rejects chat, traversal and remote origins',()=>{
 for(const path of ['/agent','/sessions','/admin/memory/../model','/admin/memory/%2e','/retrieval/arbitrary'])assert.equal(allowedAdminPath(path,'GET'),false);
 assert.equal(allowedAdminPath('/admin/memory/changes','GET'),true);assert.equal(allowedAdminPath('/retrieval/walkthrough','GET'),true);assert.equal(allowedAdminPath('/retrieval/walkthrough','POST'),false);assert.equal(allowedAdminPath('/retrieval/query','POST'),true);assert.equal(allowedAdminPath('/admin/memory','POST'),false);
 assert.equal(localOrigin('http://localhost:5190/admin.html'),true);assert.equal(localOrigin('http://127.0.0.1:5190'),true);assert.equal(localOrigin('https://localhost.evil.example'),false);assert.equal(localOrigin(undefined),false);
});
