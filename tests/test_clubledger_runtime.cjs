const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');

const html = fs.readFileSync('finance/products/clubledger-lite/index.html', 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
const storage = new Map();
const elements = new Map();
const alerts = [];
const confirms = [];
let confirmAnswer = true;

class FakeElement {
  constructor(id) {
    this.id=id; this.value=''; this.textContent=''; this.className=''; this.hidden=false;
    this.files=[]; this.listeners={}; this.children=[]; this.dataset={}; this.href=''; this.download='';
    this._innerHTML='';
  }
  addEventListener(type, fn) { (this.listeners[type] ||= []).push(fn); }
  async fire(type, event={}) {
    for (const fn of (this.listeners[type] || [])) await fn({preventDefault(){},target:this,...event});
  }
  set innerHTML(v) {
    this._innerHTML=String(v);
    if (this.id === 'period' || this.id === 'filterCategory') {
      const first = this._innerHTML.match(/<option value="([^"]*)"/);
      if (first && !this.value) this.value=first[1];
    }
    if (this.id === 'rows') {
      this.children = [...this._innerHTML.matchAll(/data-delete="([^"]+)"[^>]*aria-label="([^"]*)"/g)].map(m => {
        const btn = new FakeElement('delete');
        btn.dataset.delete=m[1]; btn.ariaLabel=m[2];
        return btn;
      });
    }
  }
  get innerHTML(){return this._innerHTML;}
  querySelectorAll(selector) { return selector==='[data-delete]' ? this.children : []; }
  click() { this.clicked=true; for (const fn of (this.listeners.click||[])) fn({target:this}); }
  remove() { this.removed=true; }
}
const ids=['period','income','expenses','net','balance','rows','empty','filterType','filterCategory','search','date','type','description','amount','category','reference','entryForm','exportBtn','backupBtn','importBtn','restoreFile'];
for (const id of ids) elements.set(id,new FakeElement(id));
elements.get('type').value='income';
elements.get('category').value='General';
elements.get('filterType').value='all';
elements.get('filterCategory').value='all';
const document = {
  getElementById(id){ if(!elements.has(id)) elements.set(id,new FakeElement(id)); return elements.get(id); },
  createElement(tag){ return new FakeElement(tag); },
  body:{appendChild(el){el.appended=true;}}
};
let uuid=0;
const context = {
  document, localStorage:{getItem:k=>storage.has(k)?storage.get(k):null,setItem:(k,v)=>storage.set(k,String(v))},
  Intl, Date, Math, Number, String, JSON, Set, Blob:class {constructor(parts,opts){this.parts=parts;this.type=opts.type;}},
  URL:{createObjectURL(blob){context.lastBlob=blob;return 'blob:test';},revokeObjectURL(){}},
  crypto:{randomUUID:()=> 'test-'+(++uuid)},
  confirm(msg){confirms.push(msg);return confirmAnswer;},
  alert(msg){alerts.push(msg);},
  console
};
vm.runInNewContext(script, context, {timeout:2000});
const fire = (id,type,event)=>elements.get(id).fire(type,event);
(async()=>{
  assert.equal(elements.get('balance').textContent.includes('0.00'),true,'initial balance');
  const date=elements.get('date').value;
  elements.get('date').value=date; elements.get('type').value='income'; elements.get('description').value='Membership dues';
  elements.get('amount').value='120.00'; elements.get('category').value='Membership'; elements.get('reference').value='RCPT-1';
  await fire('entryForm','submit');
  assert.match(elements.get('income').textContent,/120\.00/,'income total');
  assert.match(elements.get('balance').textContent,/120\.00/,'all-time balance after income');
  assert.match(storage.get('clubledger-lite-v1'),/Membership dues/,'persisted entry');

  elements.get('type').value='expense'; elements.get('description').value='Event refreshments';
  elements.get('amount').value='20.25'; elements.get('category').value='Event'; elements.get('reference').value='';
  await fire('entryForm','submit');
  assert.match(elements.get('expenses').textContent,/20\.25/,'expense total');
  assert.match(elements.get('net').textContent,/99\.75/,'monthly net');
  assert.match(elements.get('balance').textContent,/99\.75/,'all-time balance after expense');

  await fire('exportBtn','click');
  assert.match(context.lastBlob.parts.join(''),/Date","Type","Description/,'CSV has headers');
  assert.match(context.lastBlob.parts.join(''),/20\.25/,'CSV includes expense amount');
  await fire('backupBtn','click');
  const backup=JSON.parse(context.lastBlob.parts.join(''));
  assert.equal(backup.entries.length,2,'backup has two transactions');

  elements.get('restoreFile').files=[{async text(){return JSON.stringify({entries:[{id:'restore-1',date,type:'income',amountPaise:5000,description:'Restored donation',category:'Donation',reference:'R-1'}]});}}];
  await fire('restoreFile','change');
  assert.match(elements.get('balance').textContent,/50\.00/,'restore updates summary');
  assert.match(elements.get('rows').innerHTML,/Restored donation/,'restore updates table');

  const deleteButton=elements.get('rows').children[0];
  await deleteButton.fire('click');
  assert.match(elements.get('balance').textContent,/0\.00/,'delete removes transaction and recalculates balance');
  assert.ok(confirms.some(x=>x.includes('Delete')),'delete requires confirmation');
  assert.ok(alerts.some(x=>x.includes('restored')),'restore reports success');
  console.log('PASS: initial state, income, expense, monthly net, all-time balance, local persistence, CSV export, JSON backup, restore, delete confirmation, and post-delete recalculation.');
})().catch(err=>{console.error(err.stack||err);process.exitCode=1;});
