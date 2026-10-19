import test from 'node:test';
import assert from 'node:assert/strict';
import {handleRequest} from '../cloudflare/worker.mjs';
const db={prepare(){return {bind(){return this},async all(){return {results:[]}},async first(){return {total:0}},async run(){return {success:true}}}}};
const env={DB:db,ALLOWED_ORIGIN:'http://localhost:8787',RATE_LIMIT_SECRET:'test'};
test('publieke opmerkingen zijn via de toegestane herkomst leesbaar',async()=>{const response=await handleRequest(new Request('http://worker/api/comments',{headers:{Origin:'http://localhost:8787'}}),env);assert.equal(response.status,200);assert.deepEqual(await response.json(),[])});
test('andere herkomst krijgt geen toegang',async()=>{const response=await handleRequest(new Request('http://worker/api/comments',{headers:{Origin:'https://voorbeeld.nl'}}),env);assert.equal(response.status,403)});
test('lege opmerking wordt afgewezen',async()=>{const response=await handleRequest(new Request('http://worker/api/comments',{method:'POST',headers:{Origin:'http://localhost:8787','content-type':'application/json'},body:JSON.stringify({message:' ',app_version:'test'})}),env);assert.equal(response.status,400)});
