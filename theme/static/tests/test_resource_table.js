QUnit.test('Config Populated', function (assert) {
  console.log("asdf");
  //test 1 match
  assert.equal(removeQueryOccurrences("[author:mauriel ramirez] asdf")," asdf");
  //test empty string
  assert.equal(removeQueryOccurrences(""),"");
  //test zero matches
  assert.equal(removeQueryOccurrences("asdf asdf"),"asdf asdf");
});
