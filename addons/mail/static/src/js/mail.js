openerp.mail = function(session) {
    
    var mail = session.mail = {};

    /* Add ThreadDisplay widget to registry */
    session.web.form.widgets.add(
        'ThreadDisplay', 'openerp.mail.ThreadDisplay');
    session.web.page.readonly.add(
        'ThreadDisplay', 'openerp.mail.ThreadDisplay');

    /* ThreadDisplay widget: display a thread of comments */
    mail.ThreadDisplay = session.web.Widget.extend({
        // QWeb template to use when rendering the object
        template: 'ThreadDisplay',

        /**
         *
         * @params {Object} parent parent
         * @params {Object} [params]
         * @param {String} [params.res_model] res_model of mail.thread object
         * @param {Number} [params.res_id] res_id of record
         * @param {Number} [params.uid] user id
         * @param {Number} [params.char_show_more=100] number of character to display before adding a "show more"
         * @param {Number} [params.limit=10] maximum number of messages to fetch
         * @param {Number} [params.offset=0] offset for fetchign messages
         * @param {Number} [params.records=null] records to show instead of fetching messages
         */
        init: function(parent, params) {
            this._super(parent);
            console.log(parent);
            this.params = params;
            this.params.limit = this.params.limit || 10;
            this.params.offset = this.params.offset || 0;
            this.params.records = this.params.records || null;
            this.params.char_show_more = this.params.char_show_more || 100;
            // tmp
            this.map_hash = {'res.users': []};
            /* DataSets */
            this.ds = new session.web.DataSet(this, this.params.res_model);
            this.ds_users = new session.web.DataSet(this, 'res.users');
        },
        
        start: function() {
            var self = this;
            this._super.apply(this, arguments);
            /* bind buttons */
            this.$element.find('button.oe_mail_button_comment').bind('click', function () { self.do_comment(); });
            /* delegate links */
            self.$element.find('div.oe_mail_thread_display').delegate('a.intlink', 'click', function (event) {
                var res_model = event.srcElement.dataset.resModel;
                var res_id = event.srcElement.dataset.resId;
                self.do_action({
                    type: 'ir.actions.act_window',
                    res_model: res_model,
                    res_id: parseInt(res_id),
                    views: [[false, 'form']]
                });
            });
            /* display user, fetch comments */
            this.display_current_user();
            if (this.records) return this.display_comments(this.records);
            else return this.init_comments();
        },
        
        stop: function () {
            this._super.apply(this, arguments);
        },
        
        init_comments: function() {
            var self = this;
            this.params.offset = 0;
            this.$element.find('div.oe_mail_thread_display').empty();
            return this.fetch_comments().then(function () {
                self.$element.find('button.oe_mail_button_more').bind('click', function () { self.do_more(); });
            });
        },
        
        fetch_comments: function (limit, offset) {
            return this.ds.call('message_load', [[this.params.res_id], limit=(limit||this.params.limit), offset=(offset||this.params.offset)]).then(
                this.proxy('display_comments'));
        },
        
        display_comments: function (records) {
            var self = this;
            /* WIP: map matched regexp -> records to browse with name */
            _(records).each(function (record) {
                //self.check_internal_links(record.body_text);
            });
            //console.log(this.map_hash);
            _(records).each(function (record) {
                if (record.type == 'email') { record.mini_url = ('/mail/static/src/img/email_icon.png'); }
                else { record.mini_url = self.thread_get_avatar_mini('res.users', 'avatar_mini', record.user_id[0]); }
                // body text manipulation
                record.body_text = self.do_clean_text(record.body_text);
                record.tr_body_text = self.truncate_string(record.body_text, self.params.char_show_more);
                record.body_text = self.do_replace_internal_links(record.body_text);
                if (record.tr_body_text) record.tr_body_text = self.do_replace_internal_links(record.tr_body_text);
                // render
                $(session.web.qweb.render('ThreadMsg', {'record': record})).appendTo(self.$element.find('div.oe_mail_thread_display'));
                // truncated: hide full-text, show summary, add buttons
                if (record.tr_body_text) {
                    var node = self.$element.find('span.oe_mail_msg_body:last').append(' <a href="#" class="reduce">[ ... Show less]</a>');
                    self.$element.find('p.oe_mail_msg_p:last').append($('<span class="oe_mail_msg_body_short">' + record.tr_body_text + ' <a href="#" class="expand">[ ... Show more]</a></span>'));
                    var new_node = self.$element.find('span.oe_mail_msg_body_short:last');
                    node.hide();
                    node.find('a:last').click(function() {
                        node.hide(); new_node.show(); return false;
                    });
                    new_node.find('a:last').click(function() {
                        new_node.hide(); node.show(); return false;
                    });
                }
            });
            // update offset for "More" buttons
            this.params.offset += records.length;
        },
        
        display_current_user: function () {
            $('<div>').html(
                '<img src="' + this.thread_get_avatar_mini('res.users', 'avatar_mini', this.uid) + '"/>'
                ).appendTo(this.$element.find('div.oe_mail_msg_image'));
        },
        
        do_comment: function () {
            var body_text = this.$element.find('textarea').val();
            return this.ds.call('message_append_note', [[this.params.res_id], 'Reply comment', body_text, type='comment']).then(
                this.proxy('init_comments'));
        },
        
        do_more: function () {
            return this.fetch_comments(this.limit, this.offset);
        },
        
        do_replace_internal_links: function (string) {
            var self = this;
            /* shortcut to user: @login */
            var regex_login = new RegExp(/(^|\s)@(\w*)/g);
            var regex_res = regex_login.exec(string);
            while (regex_res != null) {
                var login = regex_res[2];
                var res_id = 1;
                string = string.replace(regex_res[0], '<a href="#" data-res-model="res.users" data-res-id = ' + res_id + '>@' + login + '</a>');
                regex_res = regex_login.exec(string);
            }
            return string;
        },
        
        ///* check for internal links, and map them to limitate number of queries -- WIP, probably not useful */
        //check_internal_links: function(string) {
            ///* shortcut to user: @login */
            ////var regex_login = new RegExp(/(^|\s)@(\w*[a-zA-Z_.]+\w*\s)/g);
            //var regex_login = new RegExp(/(^|\s)@(\w*)/g);
            //var regex_res = regex_login.exec(string);
            //while (regex_res != null) {
                //var login = regex_res[2];
                //this.map_hash['res.users'].push(login);
                //regex_res = regex_login.exec(string);
            //}
            ///* internal links: #res.model,name */
            //var regex_intlink = new RegExp(/(^|\s)#(\w*[a-zA-Z_]+\w*)\.(\w+[a-zA-Z_]+\w*),(\w+)/g);
            //regex_res = regex_intlink.exec(string);
            //while (regex_res != null) {
                //var res_model = regex_res[2] + '.' + regex_res[3];
                //var res_name = regex_res[4];
                //if (! (res_model in this.map_hash)) { this.map_hash[res_model] = []; }
                //this.map_hash[res_model].push(res_name);
                //regex_res = regex_intlink.exec(string);
            //}
        //},
        
        thread_get_avatar_mini: function(model, field, id) {
            return this.session.prefix + '/web/binary/image?session_id=' + this.session.session_id + '&model=' + model + '&field=' + field + '&id=' + (id || '');
        },

        truncate_string: function(string, max_length) {
            var string_len = string.length; // TODO: check for whitespaces ?
            if (string_len <= max_length) return false;
            var new_string = string.slice(0, max_length);
            return new_string;
        },
        
        do_clean_text: function (string) {
            var html = $('<div/>').text(string.replace(/\s+/g, ' ')).html().replace(new RegExp('&lt;(/)?b\\s*&gt;', 'gi'), '<$1b>');
            return html;
        },

    });


    /* Add ThreadView widget to registry */
    session.web.form.widgets.add(
        'ThreadView', 'openerp.mail.ThreadView');
    session.web.page.readonly.add(
        'ThreadView', 'openerp.mail.ThreadView');

    /* ThreadView widget: thread of comments */
    mail.ThreadView = session.web.form.Field.extend({
        // QWeb template to use when rendering the object
        form_template: 'Thread',

        init: function() {
            this.is_sub = 0;
            this.see_sub = 0;
            this._super.apply(this, arguments);
            this.thread_display = null;
            /* DataSets */
            this.ds = new session.web.DataSet(this, this.view.model);
            this.ds_users = new session.web.DataSet(this, 'res.users');
        },

        start: function() {
            var self = this;
            this._super.apply(this, arguments);
            /* bind and hide buttons */
            self.$element.find('button.oe_mail_button_followers').bind('click', function () { self.do_toggle_followers(); });
            self.$element.find('button.oe_mail_button_follow').bind('click', function () { self.do_follow(); }).hide();
            self.$element.find('button.oe_mail_button_unfollow').bind('click', function () { self.do_unfollow(); }).hide();
        },

        stop: function () {
            this._super.apply(this, arguments);
        },
        
        set_value: function() {
            var self = this;
            this._super.apply(this, arguments);
            /* hide follow/unfollow/see followers buttons */
            self.$element.find('button.oe_mail_button_follow').hide();
            self.$element.find('button.oe_mail_button_unfollow').hide();
            if (! this.view.datarecord.id) { return; }
            /* find wich (un)follow buttons to show */
            var call_res = this.ds.call('message_is_subscriber', [[this.view.datarecord.id]]).then(function (records) {
                if (records == true) { self.is_sub = 1; self.$element.find('button.oe_mail_button_unfollow').show(); }
                else { self.is_sub = 0; self.$element.find('button.oe_mail_button_follow').show(); }
                });
            /* fetch subscribers */
            this.fetch_subscribers();
            /* create ThreadDisplay widget and render it */
            this.$element.find('div.oe_mail_thread_left').empty();
            this.thread_display = new mail.ThreadDisplay(this, {'res_model': this.view.model, 'res_id': this.view.datarecord.id, 'uid': this.session.uid});
            this.thread_display.appendTo(this.$element.find('div.oe_mail_thread_left'));
        },
        
        fetch_subscribers: function () {
            var follow_res = this.ds.call('message_get_subscribers', [[this.view.datarecord.id]]).then(
                this.proxy('display_subscribers'));
            this.$element.find('div.oe_mail_followers_display').hide();
            return follow_res;
        },
        
        display_subscribers: function (records) {
            this.$element.find('div.oe_mail_followers_display').empty();
            var self = this;
            _(records).each(function (record) {
                $('<div class="oe_mail_followers_vignette">').html(
                    '<img src="' + self.thread_get_avatar_mini('res.users', 'avatar_mini', record.id) + '" title="' + record.name + '" alt="' + record.name + '"/>'
                    ).appendTo(self.$element.find('div.oe_mail_followers_display'));
            });
        },
        
        do_follow: function () {
            this.do_toggle_follow();
            return this.ds.call('message_subscribe', [[this.view.datarecord.id]]).then();
        },
        
        do_unfollow: function () {
            this.do_toggle_follow();
            return this.ds.call('message_unsubscribe', [[this.view.datarecord.id]]).then();
        },
        
        do_toggle_follow: function () {
            this.is_sub = 1 - this.is_sub;
            this.$element.find('button.oe_mail_button_unfollow').toggle();
            this.$element.find('button.oe_mail_button_follow').toggle();
        },
        
        do_toggle_followers: function () {
            this.see_sub = 1 - this.see_sub;
            if (this.see_sub == 1) { this.$element.find('button.oe_mail_button_followers').html('Hide followers'); }
            else { this.$element.find('button.oe_mail_button_followers').html('Display followers'); }
            this.$element.find('div.oe_mail_followers_display').toggle();
        },
        
        thread_get_avatar_mini: function(model, field, id) {
            id = id || '';
            var url = this.session.prefix + '/web/binary/image?session_id=' + this.session.session_id + '&model=' + model + '&field=' + field + '&id=' + id;
            return url;
        },
    });
    
    
    /* Add WallView widget to registry */
    session.web.client_actions.add('mail.all_feeds', 'session.mail.WallView');
    
    /* WallView widget: a wall of messages */
    mail.WallView = session.web.Widget.extend({
        // QWeb template to use when rendering the object
        template: 'Wall',

        init: function (parent, params) {
            this._super(parent);
            this.filter_search = params['filter_search'];
            this.search = {}
            /* DataSets */
            this.ds_msg = new session.web.DataSet(this, 'mail.message');
            this.ds_thread = new session.web.DataSet(this, 'mail.thread');
            this.ds_users = new session.web.DataSet(this, 'res.users');
        },

        start: function() {
            var self = this;
            this._super.apply(this, arguments);
            this.$element.find('button.oe_mail_button_comment').bind('click', function () { self.do_comment(); });   
            /* load mail.message search view */
            var search_view_loaded = this.load_search_view();
            var search_view_ready = $.when(search_view_loaded).then(function () {
                self.searchview.on_search.add(self.do_searchview_search);
            });
            /* fetch comments */
            var comments_ready = this.fetch_comments();
            return (search_view_ready && comments_ready);
        },
        
        stop: function () {
            this._super.apply(this, arguments);
        },
        
        load_search_view: function (view_id, defaults, hidden) {
            this.searchview = new session.web.SearchView(this, this.ds_msg, view_id || false, defaults || {}, hidden || false);
            return this.searchview.appendTo(this.$element.find('div.oe_mail_wall_search'));
        },
        
        do_searchview_search: function(domains, contexts, groupbys) {
            var self = this;
            this.rpc('/web/session/eval_domain_and_context', {
                domains: domains || [],
                contexts: contexts || [],
                group_by_seq: groupbys || []
            }, function (results) {
                self.search['context'] = results.context;
                self.search['domain'] = results.domain;
                self.search['groupby'] = results.group_by;
                self.fetch_comments(self.search['domain'], self.search['context']);
            });
        },
        
        fetch_comments: function (domain, context, offset, limit) {
            var load_res = this.ds_thread.call('get_pushed_messages',
                [[this.session.uid], limit = (limit || 100), offset = (offset || 0), domain = (domain || null), context = (context || null) ]).then(
                    this.proxy('display_comments'));
            return load_res;
        },
        
        display_comments: function (records) {
            this.$element.find('div.oe_mail_wall_threads').empty();
            sorted_records = this.sort_comments(records);
            var self = this;
            _(sorted_records).each(function (rec_models, model) { // each model
                _(rec_models).each(function (record_id, id) { // each record
                    var template = 'WallThreadContainer';
                    var render_res = session.web.qweb.render(template, {
                        'record_model': model,
                        'record_id': id,
                    });
                    $('<div class="oe_mail_wall_thread">').html(render_res).appendTo(self.$element.find('div.oe_mail_wall_threads'));
                    self.thread_display = new mail.ThreadDisplay(self,
                        {'res_model': model, 'res_id': parseInt(id), 'uid': self.session.uid, 'records': record_id}
                        );
                    self.thread_display.appendTo(self.$element.find('div.oe_mail_wall_thread_content:last'));
                });
            });
        },

        sort_comments: function (records) {
            sorted_comments = {};
            _(records).each(function (record) {
                if (! (record.model in sorted_comments)) { sorted_comments[record.model] = {}; }
                if (! (record.res_id in sorted_comments[record.model])) {
                    sorted_comments[record.model][record.res_id] = []; }
                sorted_comments[record.model][record.res_id].push(record);
            });
            return sorted_comments;
        },

        do_comment: function () {
            var body_text = this.$element.find('textarea').val();
            return this.ds_users.call('message_append_note', [[this.session.uid], 'Tweet', body_text, type='comment']).then(
                this.proxy('fetch_comments'));
        },

        thread_get_mini: function(model, field, id) {
            id = id || '';
            var url = this.session.prefix + '/web/binary/image?session_id=' + this.session.session_id + '&model=' + model + '&field=' + field + '&id=' + id;
            return url;
        },
    });
};

// vim:et fdc=0 fdl=0 foldnestmax=3 fdm=syntax:
