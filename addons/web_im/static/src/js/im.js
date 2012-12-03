
openerp.web_im = function(instance) {

    var USERS_LIMIT = 20;
    var ERROR_DELAY = 5000;

    var _t = instance.web._t,
       _lt = instance.web._lt;
    var QWeb = instance.web.qweb;

    instance.web.UserMenu.include({
        do_update: function(){
            var self = this;
            this.update_promise.then(function() {
                var im = new instance.web_im.InstantMessaging(self);
                im.appendTo(instance.client.$el);
                var button = new instance.web_im.ImTopButton(this);
                button.on("clicked", im, im.switch_display);
                button.appendTo(instance.webclient.$el.find('.oe_systray'));
            });
            return this._super.apply(this, arguments);
        },
    });

    instance.web_im.ImTopButton = instance.web.Widget.extend({
        template:'ImTopButton',
        events: {
            "click": "clicked",
        },
        clicked: function() {
            this.trigger("clicked");
        },
    });

    instance.web_im.InstantMessaging = instance.web.Widget.extend({
        template: "InstantMessaging",
        events: {
            "keydown .oe_im_searchbox": "input_change",
            "keyup .oe_im_searchbox": "input_change",
            "change .oe_im_searchbox": "input_change",
        },
        init: function(parent) {
            this._super(parent);
            this.shown = false;
            this.set("right_offset", 0);
            this.set("current_search", "");
            this.last = null;
            this.users = [];
            this.activated = false;
            this.c_manager = new instance.web_im.ConversationManager(this);
            this.on("change:right_offset", this.c_manager, _.bind(function() {
                this.c_manager.set("right_offset", this.get("right_offset"));
            }, this));
            this.user_search_dm = new instance.web.DropMisordered();
            this.users_cache = {};
        },
        start: function() {
            this.$el.css("right", -this.$el.outerWidth());
            $(window).scroll(_.bind(this.calc_box, this));
            $(window).resize(_.bind(this.calc_box, this));
            this.calc_box();

            this.on("change:current_search", this, this.search_changed);
            this.search_changed();

            var self = this;

            return this.ensure_users([instance.session.uid]).then(function() {
                var me = self.users_cache[instance.session.uid];
                delete self.users_cache[instance.session.uid];
                self.c_manager.set_me(me);
                return new instance.web.Model("im.message").call("activated", [], {context: new instance.web.CompoundContext()}).then(function(activated) {
                    if (activated) {
                        self.activated = true;
                        self.poll();
                    }
                });
            });
        },
        calc_box: function() {
            var $topbar = instance.client.$(".oe_topbar");
            var top = $topbar.offset().top + $topbar.height();
            top = Math.max(top - $(window).scrollTop(), 0);
            this.$el.css("top", top);
            this.$el.css("bottom", 0);
        },
        input_change: function() {
            this.set("current_search", this.$(".oe_im_searchbox").val());
        },
        search_changed: function(e) {
            var users = new instance.web.Model("res.users");
            var self = this;
            return this.user_search_dm.add(users.query(["name", "im_status"])
                    .filter([["name", "ilike", this.get("current_search")]])
                    .limit(USERS_LIMIT).all()).then(function(result) {
                self.add_to_user_cache(result);
                self.$(".oe_im_input").val("");
                var old_users = self.users;
                self.users = [];
                _.each(result, function(user) {
                    var widget = new instance.web_im.UserWidget(self, self.get_user(user.id));
                    widget.appendTo(self.$(".oe_im_users"));
                    widget.on("activate_user", self, self.activate_user);
                    self.users.push(widget);
                });
                _.each(old_users, function(user) {
                    user.destroy();
                });
            });
        },
        ensure_users: function(user_ids) {
            var no_cache = {};
            _.each(user_ids, function(el) {
                if (! this.users_cache[el])
                    no_cache[el] = el;
            }, this);
            var self = this;
            if (_.size(no_cache) === 0)
                return $.when();
            else
                return new instance.web.Model("res.users").call("read", [_.values(no_cache), ["name", "im_status"]],
                        {context: new instance.web.CompoundContext()}).then(function(users) {
                    self.add_to_user_cache(users);
                });
        },
        add_to_user_cache: function(user_recs) {
            _.each(user_recs, function(user_rec) {
                if (! this.users_cache[user_rec.id]) {
                    var user = new instance.web_im.ImUser(this, user_rec);
                    this.users_cache[user_rec.id] = user;
                    user.on("destroyed", this, function() {
                        delete this.users_cache[user_rec.id];
                    });
                }
            }, this);
        },
        get_user: function(user_id) {
            return this.users_cache[user_id];
        },
        switch_display: function() {
            var fct =  _.bind(function(place) {
                this.set("right_offset", place + this.$el.outerWidth());
            }, this);
            var opt = {
                step: fct,
            };
            if (this.shown) {
                this.$el.animate({
                    right: -this.$el.outerWidth(),
                }, opt);
            } else {
                if (! this.activated) {
                    this.do_warn("Instant Messaging is not activated on this server.", "");
                    return;
                }
                this.$el.animate({
                    right: 0,
                }, opt);
            }
            this.shown = ! this.shown;
        },
        poll: function() {
            var self = this;
            var user_ids = _.map(this.users_cache, function(el) {
                return el.get("id");
            });
            this.rpc("/im/poll", {
                last: this.last,
                users_watch: user_ids,
                context: instance.web.pyeval.eval('context', {}),
            }, {shadow: true}).then(function(result) {
                _.each(result.users_status, function(el) {
                    self.get_user(el.id).set(el);
                });
                self.last = result.last;
                var user_ids = _.pluck(_.pluck(result.res, "from"), 0);
                self.ensure_users(user_ids).then(function() {
                    _.each(result.res, function(mes) {
                        var user = self.get_user(mes.from[0]);
                        self.c_manager.received_message(mes, user);
                    });
                    self.poll();
                });
            }, function(unused, e) {
                e.preventDefault();
                setTimeout(_.bind(self.poll, self), ERROR_DELAY);
            });
        },
        activate_user: function(user) {
            this.c_manager.activate_user(user);
        },
    });

    instance.web_im.UserWidget = instance.web.Widget.extend({
        "template": "UserWidget",
        events: {
            "click": "activate_user",
        },
        init: function(parent, user) {
            this._super(parent);
            this.user = user;
            this.user.add_watcher();
        },
        start: function() {
            var change_status = function() {
                this.$(".oe_im_user_online").toggle(this.user.get("im_status") === true);
            };
            this.user.on("change:im_status", this, change_status);
            change_status.call(this);
        },
        activate_user: function() {
            this.trigger("activate_user", this.user);
        },
        destroy: function() {
            this.user.remove_watcher();
            this._super();
        },
    });

    instance.web_im.ImUser = instance.web.Class.extend(instance.web.PropertiesMixin, {
        init: function(parent, user_rec) {
            instance.web.PropertiesMixin.init.call(this, parent);
            user_rec.image_url = instance.session.url('/web/binary/image', {model:'res.users', field: 'image_small', id: user_rec.id});
            this.set(user_rec);
            this.set("watcher_count", 0);
            this.on("change:watcher_count", this, function() {
                if (this.get("watcher_count") === 0)
                    this.destroy();
            });
        },
        destroy: function() {
            this.trigger("destroyed");
            instance.web.PropertiesMixin.destroy.call(this);
        },
        add_watcher: function() {
            this.set("watcher_count", this.get("watcher_count") + 1);
        },
        remove_watcher: function() {
            this.set("watcher_count", this.get("watcher_count") - 1);
        },
    });

    instance.web_im.ConversationManager = instance.web.Controller.extend({
        init: function(parent) {
            this._super(parent);
            this.set("right_offset", 0);
            this.conversations = [];
            this.users = {};
            this.on("change:right_offset", this, this.calc_positions);
        },
        set_me: function(me) {
            this.me = me;
        },
        activate_user: function(user) {
            if (this.users[user.get('id')]) {
                return this.users[user.get('id')];
            }
            var conv = new instance.web_im.Conversation(this, user, this.me);
            conv.appendTo(instance.client.$el);
            conv.on("destroyed", this, function() {
                this.conversations = _.without(this.conversations, conv);
                delete this.users[conv.user.get('id')];
                this.calc_positions();
            });
            this.conversations.push(conv);
            this.users[user.get('id')] = conv;
            this.calc_positions();
            return conv;
        },
        received_message: function(message, user) {
            var conv = this.activate_user(user);
            conv.received_message(message);
        },
        calc_positions: function() {
            var current = this.get("right_offset");
            _.each(_.range(this.conversations.length), function(i) {
                this.conversations[i].set("right_position", current);
                current += this.conversations[i].$el.outerWidth(true);
            }, this);
        },
    });

    instance.web_im.Conversation = instance.web.Widget.extend({
        "template": "Conversation",
        events: {
            "keydown input": "send_message",
            "click .oe_im_chatview_close": "destroy",
            "click .oe_im_chatview_header": "show_hide",
        },
        init: function(parent, user, me) {
            this._super(parent);
            this.me = me;
            this.user = user;
            this.user.add_watcher();
            this.set("right_position", 0);
            this.shown = true;
        },
        start: function() {
            var change_status = function() {
                this.$(".oe_im_chatview_online").toggle(this.user.get("im_status") === true);
                this.$(".oe_im_chatview_disconnected").toggle(this.user.get("im_status") === false);
            };
            this.user.on("change:im_status", this, change_status);
            change_status.call(this);

            this.on("change:right_position", this, this.calc_pos);
            this.full_height = this.$el.height();
            this.calc_pos();
        },
        show_hide: function() {
            if (this.shown) {
                this.$el.animate({
                    height: this.$(".oe_im_chatview_header").outerHeight(),
                });
            } else {
                this.$el.animate({
                    height: this.full_height,
                });
            }
            this.shown = ! this.shown;
        },
        calc_pos: function() {
            this.$el.css("right", this.get("right_position"));
        },
        received_message: function(message) {
            this._add_bubble(this.user, message.message, message.date);
        },
        send_message: function(e) {
            if(e && e.which !== 13) {
                return;
            }
            var mes = this.$("input").val();
            this.$("input").val("");
            this._add_bubble(this.me, mes, instance.web.datetime_to_str(new Date()));
            var model = new instance.web.Model("im.message");
            model.call("post", [mes, this.user.get('id')], {context: new instance.web.CompoundContext()});
        },
        _add_bubble: function(user, item, date) {
            var items = [item];
            if (user === this.last_user) {
                this.last_bubble.remove();
                items = this.last_items.concat(items);
            }
            this.last_user = user;
            this.last_items = items;
            date = instance.web.str_to_datetime(date);
            date = date.toString(Date.CultureInfo.formatPatterns.shortDate + " " + Date.CultureInfo.formatPatterns.shortTime);
            this.last_bubble = $(QWeb.render("Conversation.bubble", {"items": items, "user": user, "time": date}));
            $(this.$(".oe_im_chatview_content").children()[0]).append(this.last_bubble);
            this.$(".oe_im_chatview_content").scrollTop($(this.$(".oe_im_chatview_content").children()[0]).height());
        },
        destroy: function() {
            this.user.remove_watcher();
            this.trigger("destroyed");
            return this._super();
        },
    });

}