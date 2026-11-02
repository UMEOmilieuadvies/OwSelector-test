import assert from 'node:assert/strict';
import fs from 'node:fs';

const css = fs.readFileSync('css/app.css', 'utf8');
assert.match(css, /@media\(max-width:980px\)/, 'Een tabletgrens voor de hoofdindeling ontbreekt.');
assert.match(css, /\.workspace\{display:grid;grid-template-columns:minmax\(0,1fr\)/, 'Op een tablet moet de werkruimte onder elkaar staan.');
assert.match(css, /\.resizer\{display:none\}/, 'Kolomslepers mogen op een smal scherm niet zichtbaar blijven.');
assert.match(css, /\.regulationPicker\{grid-column:1\/-1/, 'De regelingskeuze moet onder de zoekbalk kunnen doorlopen.');
console.log('Responsieve hoofdindeling voor tablet en telefoon is gecontroleerd.');
