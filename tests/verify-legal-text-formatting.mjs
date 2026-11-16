import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const graphDir='data/graph';
if(!fs.existsSync(graphDir)){
  console.log('Opmaakcontrole overgeslagen: graph-bestanden worden pas tijdens de build samengesteld.');
  process.exit(0);
}

const graphFiles=fs.readdirSync(graphDir).filter(file=>file.endsWith('_legal_graph.json'));
assert.ok(graphFiles.length>=7,'Voor de opmaakcontrole moeten alle juridische graph-bestanden beschikbaar zijn.');

const forbidden=[
  ['tab',/\t/],
  ['harde spatie',/\u00a0/],
  ['zachte afbreking',/\u00ad/],
  ['onzichtbaar teken',/[\u200b-\u200d\ufeff]/],
  ['regeleinde',/[\r\n]/],
  ['overtollige spaties',/ {2,}/]
];
const findings=[];

function inspect(value,file,location=''){
  if(typeof value==='string'){
    for(const [label,pattern] of forbidden){
      if(pattern.test(value))findings.push(`${file}:${location || '<tekst>'} bevat ${label}`);
    }
    return;
  }
  if(Array.isArray(value)){
    value.forEach((item,index)=>inspect(item,file,`${location}[${index}]`));
    return;
  }
  if(value&&typeof value==='object'){
    for(const [key,item] of Object.entries(value))inspect(item,file,location?`${location}.${key}`:key);
  }
}

for(const file of graphFiles){
  inspect(JSON.parse(fs.readFileSync(path.join(graphDir,file),'utf8')),file);
}

assert.deepEqual(findings,[],`Ongewenste bronopmaak gevonden:\n${findings.slice(0,30).join('\n')}`);
console.log(`Juridische tekstformattering is gecontroleerd in ${graphFiles.length} regelingen.`);
