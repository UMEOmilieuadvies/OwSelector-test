import fs from 'node:fs';
import {fingerprints,read} from './promotion-fingerprint.mjs';
const args=process.argv.slice(2);const value=name=>args[args.indexOf(name)+1];
const output=value('--output');const commit=value('--commit');
if(!output||!commit)throw new Error('Gebruik --output en --commit.');
const version=read(process.cwd(),'VERSION').trim();
const candidate={schema:1,environment:'test',test_version:version,test_commit:commit,fingerprints:fingerprints(process.cwd())};
fs.writeFileSync(output,JSON.stringify(candidate,null,2)+'\n','utf8');
console.log(`Promotiekandidaat ${version} is vastgelegd.`);