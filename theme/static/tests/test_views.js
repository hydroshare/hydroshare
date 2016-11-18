QUnit.test('Config Populated', function (assert) {
    assert.ok(config.views);
    assert.ok(config.views.UploadListingView);
    assert.ok(config.views.NewUploadView);
    assert.ok(config.views.LoginView);
});

QUnit.module('UploadListingView Tests', {
    beforeEach: function () {
        $('#qunit-fixture').append($('<div>', {id: 'files'}));
        this.view = new config.views.UploadListingView();
    },
    afterEach: function () {
        this.view.remove();
    }
});

QUnit.test('Add Upload', function (assert) {
    var uploads = new config.collections.UploadCollection(),
        upload = uploads.push({
            name: 'test.png',
            size: 200,
            created: '2015-01-14T01:21:56.870',
            links: {
                self: '/uploads/test.png'
            }
        });
    this.view.addFile(upload);
    assert.equal($('.file', this.view.$el).length, 1);
});

QUnit.module('NewUploadView Tests', {
    beforeEach: function () {
        $('#qunit-fixture').append($('<div>', {id: 'upload'}));
        this.uploads = new config.collections.UploadCollection();
        this.view = new config.views.NewUploadView({uploads: this.uploads});
        sinon.stub(this.uploads, 'create');
    },
    afterEach: function () {
        this.view.remove();
        this.uploads.create.restore();
    }
});

QUnit.test('Drag Enter', function (assert) {
    var e = $.Event('dragenter');
    this.view.enter(e);
    assert.equal(this.view.enter(e), false);
    assert.ok(this.view.$el.hasClass('hover'));
});

QUnit.test('Drag Over', function (assert) {
    var e = $.Event('dragover');
    assert.equal(this.view.over(e), false);
    assert.ok(this.view.$el.hasClass('hover'));
});

QUnit.test('Drag End', function (assert) {
    var e = $.Event('dragend');
    this.view.$el.addClass('hover');
    this.view.end(e);
    assert.equal(this.view.$el.hasClass('hover'), false);
});

QUnit.test('Drop File', function (assert) {
    var e = $.Event('drop'),
        file = {'name': 'test.txt'};
    e.originalEvent = {
        dataTransfer: {files: [file, ]}
    };
    this.view.$el.addClass('hover');
    this.view.drop(e);
    assert.ok(this.uploads.create.calledOnce);
    assert.equal(this.view.$el.hasClass('hover'), false);
});
