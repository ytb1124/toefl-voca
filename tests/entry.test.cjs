const test = require('node:test');
const assert = require('node:assert/strict');
const destination = require('../study/entry.js');

test('existing public address opens the integrated study home', () => {
  assert.equal(destination('https://taebin.link/toefl-voca/fillintheblank.html'),
    'https://taebin.link/toefl-voca/study/index.html');
});
test('all 49 Task links keep the original C-Test page', () => {
  for (let n = 1; n <= 49; n++) {
    assert.equal(destination(`https://taebin.link/toefl-voca/fillintheblank.html?task=${n}`), null);
  }
  assert.equal(destination('https://taebin.link/toefl-voca/fillintheblank.html?classic=1'), null);
});
test('relative routing works for local previews and file copies', () => {
  assert.equal(destination('http://127.0.0.1:8871/fillintheblank.html'),
    'http://127.0.0.1:8871/study/index.html');
  assert.equal(destination('file:///Users/example/Study/fillintheblank.html'),
    'file:///Users/example/Study/study/index.html');
});
