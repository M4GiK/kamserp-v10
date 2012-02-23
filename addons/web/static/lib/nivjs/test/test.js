
module("Class");

test("Class exists", function() {
	ok(!!niv.Class, "Class does not exist");
	ok(!!niv.Class.extend, "extend does not exist");
});

test("Inheritance works", function() {
    var Claz = niv.Class.extend({
        test: function() {
            return "ok";
        }
    })
    equal("ok", new Claz().test());
});

module("DestroyableMixin");

test("DestroyableMixin works", function() {
    var Claz = niv.Class.extend(_.extend({}, niv.DestroyableMixin, {}));
    var x = new Claz();
    equal(false, !!x.isDestroyed());
    x.destroy();
    equal(true, x.isDestroyed());
});

module("ParentedMixin");

test("ParentedMixin works", function() {
    var Claz = niv.Class.extend(_.extend({}, niv.ParentedMixin, {}));
    var x = new Claz();
    var y = new Claz();
    y.setParent(x);
    equal(x, y.getParent());
    equal(y, x.getChildren()[0]);
    x.destroy();
    equal(true, y.isDestroyed());
});
