openerp.mail = function(session) {
    
    var mail = session.mail = {};

    /* Add ThreadDisplay widget to registry */
    session.web.form.widgets.add(
        'Thread', 'openerp.mail.Thread');
    session.web.page.readonly.add(
        'Thread', 'openerp.mail.Thread');

    /** 
     * ThreadDisplay widget: this widget handles the display of a thread of
     * messages. The [thread_level] parameter sets the thread level number:
     * - root message
     * - - sub message (parent_id = root message)
     * - - - sub sub message (parent id = sub message)
     * - - sub message (parent_id = root message)
     * This widget has 2 ways of initialization, either you give records to be rendered,
     * either it will fetch [limit] messages related to [res_model]:[res_id].
     */
    mail.Thread = session.web.Widget.extend({
        template: 'Thread',

        /**
         * @param {Object} parent parent
         * @param {Object} [params]
         * @param {String} [params.res_model] res_model of mail.thread object
         * @param {Number} [params.res_id] res_id of record
         * @param {Number} [params.parent_id=false] parent_id of message
         * @param {Number} [params.uid] user id
         * @param {Number} [params.thread_level=0] number of levels in the thread (only 0 or 1 currently)
         * @param {Number} [params.msg_more_limit=100] number of character to display before having a "show more" link;
         *                                             note that the text will not be truncated if it does not have 110% of
         *                                             the parameter (ex: 110 characters needed to be truncated and be displayed
         *                                             as a 100-characters message)
         * @param {Number} [params.limit=10] maximum number of messages to fetch
         * @param {Number} [params.offset=0] offset for fetching messages
         * @param {Number} [params.records=null] records to show instead of fetching messages
         */
        init: function(parent, params) {
            this._super(parent);
            this.params = params;
            this.params.parent_id = this.params.parent_id || false;
            this.params.thread_level = this.params.thread_level || 0;
            this.params.msg_more_limit = this.params.msg_more_limit || 100;
            this.params.limit = this.params.limit || 100;
            this.params.offset = this.params.offset || 0;
            this.params.records = this.params.records || null;
            // datasets and internal vars
            this.ds = new session.web.DataSet(this, this.params.res_model);
            this.ds_users = new session.web.DataSet(this, 'res.users');
            this.ds_msg = new session.web.DataSet(this, 'mail.message');
            this.sorted_comments = {'root_ids': [], 'root_id_msg_list': {}};
            // display customization vars
            this.display = {};
            this.display.show_post_comment = this.params.show_post_comment || false;
            this.display.show_reply = (this.params.thread_level > 0);
            this.display.show_delete = true;
            this.display.show_hide = this.params.show_hide || false;
            this.display.show_more = (this.params.thread_level == 0);
            // not used currently
            this.intlinks_mapping = {};
        },
        
        start: function() {
            this._super.apply(this, arguments);
            // customize display
            if (! this.display.show_post_comment) this.$element.find('div.oe_mail_thread_act').hide();
            //if (this.display.show_more) this.$element.find('div.oe_mail_thread_more').show();
            // add events
            this.add_events();
            /* display user, fetch comments */
            this.display_current_user();
            if (this.params.records) var display_done = this.fetch_comments_tmp(this.params.records);
            else var display_done = this.init_comments();
            return display_done
        },
        
        add_events: function() {
            var self = this;
            // event: click on 'more' at bottom of thread
            this.$element.find('button.oe_mail_button_more').click(function () {
                self.do_more();
            });
            // event: writing in textarea
            this.$element.find('textarea.oe_mail_action_textarea').keyup(function (event) {
                var charCode = (event.which) ? event.which : window.event.keyCode;
                if (event.shiftKey && charCode == 13) { this.value = this.value+"\n"; }
                else if (charCode == 13) { self.do_comment(); }
            });
            // event: click on 'reply' in msg
            this.$element.find('div.oe_mail_thread_display').delegate('a.oe_mail_msg_reply', 'click', function (event) {
               var act_dom = $(this).parents('div.oe_mail_thread_display').find('div.oe_mail_thread_act:first');
               act_dom.toggle();
            });
            // event: click on 'delete' in msg
            this.$element.find('div.oe_mail_thread_display').delegate('a.oe_mail_msg_delete', 'click', function (event) {
               //console.log('deleting');
               var msg_id = event.srcElement.dataset.id;
               if (! msg_id) return false;
               var call_defer = self.ds_msg.unlink([parseInt(msg_id)]);
               $(event.srcElement).parents('li.oe_mail_thread_msg').eq(0).hide();
               if (self.params.thread_level > 0) {
                   $(event.srcElement).parents('ul.oe_mail_thread').eq(0).hide();
               }
               return false;
            });
            // event: click on 'hide' in msg
            this.$element.find('div.oe_mail_thread_display').delegate('a.oe_mail_msg_hide', 'click', function (event) {
               //console.log('hiding');
               var msg_id = event.srcElement.dataset.id;
               if (! msg_id) return false;
               //console.log(msg_id);
               var call_defer = self.ds.call('message_remove_pushed_notif', [[self.params.res_id], [parseInt(msg_id)], true]);
               $(event.srcElement).parents('li.oe_mail_thread_msg').eq(0).hide();
               if (self.params.thread_level > 0) {
                   $(event.srcElement).parents('ul.oe_mail_thread').eq(0).hide();
               }
               return false;
            });
            // event: click on an internal link
            this.$element.find('div.oe_mail_thread_display').delegate('a.intlink', 'click', function (event) {
                // lazy implementation: fetch data and try to redirect
                if (! event.srcElement.dataset.resModel) return false;
                else var res_model = event.srcElement.dataset.resModel;
                var res_login = event.srcElement.dataset.resLogin;
                var res_id = event.srcElement.dataset.resId;
                if ((! res_login) && (! res_id)) return false;
                if (! res_id) {
                    var ds = new session.web.DataSet(self, res_model);
                    var defer = ds.call('search', [[['login', '=', res_login]]]).then(function (records) {
                        if (records[0]) {
                            self.do_action({ type: 'ir.actions.act_window', res_model: res_model, res_id: parseInt(records[0]), views: [[false, 'form']]});
                        }
                        else return false;
                    });
                }
                else self.do_action({ type: 'ir.actions.act_window', res_model: res_model, res_id: parseInt(res_id), views: [[false, 'form']]});
            });
        },
        
        destroy: function () {
            this._super.apply(this, arguments);
        },
        
        init_comments: function() {
            var self = this;
            this.params.offset = 0;
            this.sorted_comments = {'root_ids': [], 'root_id_msg_list': {}};
            this.$element.find('div.oe_mail_thread_display').empty();
            domain = this.get_fetch_domain(this.sorted_comments);
            return this.fetch_comments(this.params.limit, this.params.offset, domain).then();
        },
        
        fetch_comments_tmp: function (records_good) {
            console.log('fetch comments tmp');
            var self = this;
            var defer = this.ds.call('message_load', [[this.params.res_id], 1, 0, [ ['id', 'child_of', this.params.parent_id], ['id', '!=', this.params.parent_id]] ]);
            $.when(defer).then(function (records) {
                //console.log(records);
                if (records.length <= 0) self.display.show_more = false;
                self.display_comments(records_good);
                if (self.display.show_more == true) self.$element.find('div.oe_mail_thread_more:last').show();
                else self.$element.find('div.oe_mail_thread_more:last').hide();
                });
            return defer;
        },
        
        fetch_comments: function (limit, offset, domain) {
            //console.log('fetch comments');
            var self = this;
            var defer = this.ds.call('message_load', [[this.params.res_id], ( (limit+1)||(this.params.limit+1) ), (offset||this.params.offset), (domain||[]), (this.params.thread_level > 0), (this.sorted_comments['root_ids'])]);
            $.when(defer).then(function (records) {
                if (records.length <= self.params.limit) self.display.show_more = false;
                else records.pop();
                self.display_comments(records);
                if (self.display.show_more == true) self.$element.find('div.oe_mail_thread_more:last').show();
                else  self.$element.find('div.oe_mail_thread_more:last').hide();
                });
            return defer;
        },

        display_comments: function (records) {
            var self = this;
            if (this.params.thread_level > 0) {
                this.sc = this.sort_comments(records);
            }
        
            /* WIP: map matched regexp -> records to browse with name */
            //_(records).each(function (record) {
                //self.do_check_internal_links(record.body_text);
            //});
            
            _(records).each(function (record) {
                var sub_msgs = [];
                if ((record.parent_id == false || record.parent_id[0] == self.params.parent_id) && self.params.thread_level > 0 ) {
                    var sub_list = self.sc['root_id_msg_list'][record.id];
                    _(records).each(function (record) {
                        if (record.parent_id == false || record.parent_id[0] == self.params.parent_id) return;
                        if (_.indexOf(_.pluck(sub_list, 'id'), record.id) != -1) {
                            sub_msgs.push(record);
                        }
                    });
                    self.display_comment(record);
                    self.thread = new mail.Thread(self, {'res_model': self.params.res_model, 'res_id': self.params.res_id, 'uid': self.params.uid,
                                                            'records': sub_msgs, 'thread_level': (self.params.thread_level-1), 'parent_id': record.id});
                    self.$element.find('div.oe_mail_thread_display:last').append('<div class="oe_mail_thread_subthread"/>');
                    self.thread.appendTo(self.$element.find('div.oe_mail_thread_subthread:last'));
                }
                else if (self.params.thread_level == 0) {
                    self.display_comment(record);
                }
            });
            // update offset for "More" buttons
            if (this.params.thread_level == 0) this.params.offset += records.length;
        },

        /**
         * Display a record
         */
        display_comment: function (record) {
            if (record.type == 'email') { record.mini_url = ('/mail/static/src/img/email_icon.png'); }
            else { record.mini_url = this.thread_get_avatar('res.users', 'avatar', record.user_id[0]); }    
            // body text manipulation
            record.body_text = this.do_clean_text(record.body_text);
            record.tr_body_text = this.do_truncate_string(record.body_text, this.params.msg_more_limit);
            record.body_text = this.do_replace_internal_links(record.body_text);
            if (record.tr_body_text) record.tr_body_text = this.do_replace_internal_links(record.tr_body_text);
            // render
            $(session.web.qweb.render('ThreadMsg', {'record': record, 'thread': this, 'params': this.params, 'display': this.display})
                    ).appendTo(this.$element.children('div.oe_mail_thread_display:first'));
            // truncated: hide full-text, show summary, add buttons
            if (record.tr_body_text) {
                var node_body = this.$element.find('span.oe_mail_msg_body:last').append(' <a href="#" class="reduce">[ ... Show less]</a>');
                var node_body_short = this.$element.find('span.oe_mail_msg_body_short:last').append(' <a href="#" class="expand">[ ... Show more]</a>');
                node_body.hide();
                node_body.find('a:last').click(function() { node_body.hide(); node_body_short.show(); return false; });
                node_body_short.find('a:last').click(function() { node_body_short.hide(); node_body.show(); return false; });
            }
        },
       
        /**
         * Add records to sorted_comments array
         * @param {Array} records records from mail.message sorted by date desc
         * @returns {Object} sc sorted_comments: dict {
         *                          'root_id_list': list or root_ids
         *                          'root_id_msg_list': {'record_id': [ancestor_ids]}, still sorted by date desc
         *                          'id_to_root': {'root_id': [records]}, still sorted by date desc
         *                          }
         */
        sort_comments: function (records) {
            var self = this;
            sc = {'root_id_list': [], 'root_id_msg_list': {}, 'id_to_root': {}}
            var cur_iter = 0; var max_iter = 10; var modif = true;
            /* step1: get roots */
            while ( modif && (cur_iter++) < max_iter) {
                modif = false;
                _(records).each(function (record) {
                    if ( (record.parent_id == false || record.parent_id[0] == self.params.parent_id) && (_.indexOf(sc['root_id_list'], record.id) == -1)) {
                        sc['root_id_list'].push(record.id);
                        sc['root_id_msg_list'][record.id] = [];
                        self.sorted_comments['root_ids'].push(record.id);
                        modif = true;
                    } 
                    else {
                        if (_.indexOf(sc['root_id_list'], record.parent_id[0]) != -1) {
                             sc['id_to_root'][record.id] = record.parent_id[0];
                             modif = true;
                        }
                        else if ( sc['id_to_root'][record.parent_id[0]] ) {
                             sc['id_to_root'][record.id] = sc['id_to_root'][record.parent_id[0]];
                             modif = true;
                        }
                    }
                });
            }
            /* step2: add records */
            _(records).each(function (record) {
                var root_id = sc['id_to_root'][record.id];
                if (! root_id) return;
                sc['root_id_msg_list'][root_id].push(record);
                //self.sorted_comments['root_id_msg_list'][root_id].push(record.id);
            });
            return sc;
        },
        
        display_current_user: function () {
            return this.$element.find('img.oe_mail_msg_image').attr('src', this.thread_get_avatar('res.users', 'avatar', this.params.uid));
        },
        
        do_comment: function () {
            var comment_node = this.$element.find('textarea');
            var body_text = comment_node.val();
            comment_node.val('');
            return this.ds.call('message_append_note', [[this.params.res_id], 'Reply comment', body_text, this.params.parent_id, 'comment']).then(
                this.proxy('init_comments'));
        },
        
        /**
         * Create a domain to fetch new comments according to
         * comment already present in sorted_comments
         * @param {Object} sorted_comments (see sort_comments)
         * @returns {Array} fetch_domain (OpenERP domain style)
         */
        get_fetch_domain: function (sorted_comments) {
            var domain = [];
            var ids = sorted_comments.root_ids.slice();
            var dis2 = [];
            // must be child of current parent
            if (this.params.parent_id) { domain.push(['id', 'child_of', this.params.parent_id]); }
            // must not be children of already fetched messages
            if (ids.length > 0) {
                domain.push('&');
                domain.push('!');
                domain.push(['id', 'child_of', ids]);
            }
            // must not be current roots
            //if (this.params.parent_id != false) {
                //ids.push(this.params.parent_id);
            //}
            //if (ids.length > 0) {
                //domain.push['id', 'not in', ids]);
            //}
            
            _(sorted_comments.root_ids).each(function (id) { // each record
                ids.push(id);
                dis2.push(id);
            });
            
            if (ids.length > 0) {
                domain.push('&');
                domain.push('!');
                domain.push(['id', 'child_of', ids]);
            }
            if (this.params.parent_id != false) {
                dis2.push(this.params.parent_id);
            }
            if (dis2.length > 0) {
                domain.push(['id', 'not in', dis2]);
            }
            
            
            return domain;
        },
        
        do_more: function () {
            domain = this.get_fetch_domain(this.sorted_comments);
            //console.log(domain);
            //console.log(this.params.limit + '-' + this.params.offset + '-' + this.params.parent_id + '-' + this.params.res_id);
            //return true;
            return this.fetch_comments(this.params.limit, this.params.offset, domain);
        },
        
        do_replace_internal_links: function (string) {
            var self = this;
            /* shortcut to user: @login */
            var regex_login = new RegExp(/(^|\s)@(\w*)/g);
            var regex_res = regex_login.exec(string);
            while (regex_res != null) {
                var login = regex_res[2];
                string = string.replace(regex_res[0], '<a href="#" class="intlink oe_mail_oe_intlink" data-res-model="res.users" data-res-login = ' + login + '>@' + login + '</a>');
                regex_res = regex_login.exec(string);
            }
            return string;
        },
        
        thread_get_avatar: function(model, field, id) {
            return this.session.prefix + '/web/binary/image?session_id=' + this.session.session_id + '&model=' + model + '&field=' + field + '&id=' + (id || '');
        },
        
        do_truncate_string: function(string, max_length) {
            if (string.length <= (max_length * 1.2)) return false;
            else return string.slice(0, max_length);
        },
        
        do_clean_text: function (string) {
            var html = $('<div/>').text(string.replace(/\s+/g, ' ')).html().replace(new RegExp('&lt;(/)?(b|em)\\s*&gt;', 'gi'), '<$1$2>');
            return html;
        },
        
        /**
         *
         * var regex_login = new RegExp(/(^|\s)@(\w*[a-zA-Z_.]+\w*\s)/g);
         * var regex_login = new RegExp(/(^|\s)@(\w*)/g);
         * var regex_intlink = new RegExp(/(^|\s)#(\w*[a-zA-Z_]+\w*)\.(\w+[a-zA-Z_]+\w*),(\w+)/g);
         */
        do_check_internal_links: function(string) {
            /* shortcut to user: @login */
            var regex_login = new RegExp(/(^|\s)@(\w*)/g);
            var regex_res = regex_login.exec(string);
            while (regex_res != null) {
                var login = regex_res[2];
                if (! ('res.users' in this.map_hash)) { this.map_hash['res.users']['name'] = []; }
                this.map_hash['res.users']['login'].push(login);
                regex_res = regex_login.exec(string);
            }
            /* internal links: #res.model,name */
            var regex_intlink = new RegExp(/(^|\s)#(\w*[a-zA-Z_]+\w*)\.(\w+[a-zA-Z_]+\w*),(\w+)/g);
            regex_res = regex_intlink.exec(string);
            while (regex_res != null) {
                var res_model = regex_res[2] + '.' + regex_res[3];
                var res_name = regex_res[4];
                if (! (res_model in this.map_hash)) { this.map_hash[res_model]['name'] = []; }
                this.map_hash[res_model]['name'].push(res_name);
                regex_res = regex_intlink.exec(string);
            }
        },
        
        /** checks if tue current user is the message author */
        _is_author: function (id) {
            return (this.session.uid == id);
        },

    });


    /* Add ThreadView widget to registry */
    session.web.form.widgets.add(
        'ThreadView', 'openerp.mail.RecordThread');
    session.web.page.readonly.add(
        'ThreadView', 'openerp.mail.RecordThread');

    /* ThreadView widget: thread of comments */
    mail.RecordThread = session.web.form.Field.extend({
        // QWeb template to use when rendering the object
        form_template: 'RecordThread',

        init: function() {
            this._super.apply(this, arguments);
            this.see_subscribers = true;
            this.thread = null;
            // datasets
            this.ds = new session.web.DataSet(this, this.view.model);
            this.ds_users = new session.web.DataSet(this, 'res.users');
        },

        start: function() {
            this._super.apply(this, arguments);
            var self = this;
            // bind buttons
            this.$element.find('button.oe_mail_button_followers').click(function () { self.do_toggle_followers(); }).hide();
            this.$element.find('button.oe_mail_button_follow').click(function () { self.do_follow(); })
                .mouseover(function () { $(this).html('Follow'); }).mouseleave(function () { $(this).html('Not following'); });
            this.$element.find('button.oe_mail_button_unfollow').click(function () { self.do_unfollow(); })
                .mouseover(function () { $(this).html('Unfollow'); }).mouseleave(function () { $(this).html('Following'); });
            this.reinit();
        },

        destroy: function () {
            this._super.apply(this, arguments);
        },
        
        reinit: function() {
            this.see_subscribers = true;
            this.$element.find('button.oe_mail_button_followers').html('Hide followers')
            this.$element.find('button.oe_mail_button_follow').hide();
            this.$element.find('button.oe_mail_button_unfollow').hide();
        },
        
        set_value: function() {
            this._super.apply(this, arguments);
            var self = this;
            this.reinit();
            if (! this.view.datarecord.id) { this.$element.find('ul.oe_mail_thread').hide(); return; }
            // fetch followers
            var fetch_sub_done = this.fetch_subscribers();
            // create and render Thread widget
            this.$element.find('div.oe_mail_recthread_left').empty();
            if (this.thread) this.thread.destroy();
            this.thread = new mail.Thread(this, {'res_model': this.view.model, 'res_id': this.view.datarecord.id, 'uid': this.session.uid,
                            'show_post_comment': true, 'limit': 15});
            var thread_done = this.thread.appendTo(this.$element.find('div.oe_mail_recthread_left'));
            return fetch_sub_done && thread_done;
        },
        
        fetch_subscribers: function () {
            return this.ds.call('message_get_subscribers', [[this.view.datarecord.id]]).then(this.proxy('display_subscribers'));
        },
        
        display_subscribers: function (records) {
            var self = this;
            this.is_subscriber = false;
            var sub_node = this.$element.find('div.oe_mail_recthread_followers')
            sub_node.empty();
            $('<h4/>').html('Followers (' + records.length + ')').appendTo(sub_node);
            _(records).each(function (record) {
                if (record.id == self.session.uid) { self.is_subscriber = true; }
                var mini_url = self.thread_get_avatar('res.users', 'avatar', record.id);
                $('<img class="oe_mail_oe_left oe_mail_msg_image" src="' + mini_url + '" title="' + record.name + '" alt="' + record.name + '"/>').appendTo(sub_node);
            });
            if (self.is_subscriber) {
                self.$element.find('button.oe_mail_button_follow').hide();
                self.$element.find('button.oe_mail_button_unfollow').show(); }
            else {
                self.$element.find('button.oe_mail_button_follow').show();
                self.$element.find('button.oe_mail_button_unfollow').hide(); }
        },
        
        do_follow: function () {
            return this.ds.call('message_subscribe', [[this.view.datarecord.id]]).pipe(this.proxy('fetch_subscribers'));
        },
        
        do_unfollow: function () {
            var self = this;
            return this.ds.call('message_unsubscribe', [[this.view.datarecord.id]]).then(function (record) {
                if (record == false) self.do_notify("Impossible to unsubscribe", "You are automatically subscribed to this record. You cannot unsubscribe.");
                }).pipe(this.proxy('fetch_subscribers'));
        },
        
        do_toggle_followers: function () {
            this.see_subscribers = ! this.see_subscribers;
            if (this.see_subscribers) { this.$element.find('button.oe_mail_button_followers').html('Hide followers'); }
            else { this.$element.find('button.oe_mail_button_followers').html('Display followers'); }
            this.$element.find('div.oe_mail_recthread_followers').toggle();
        },
        
        thread_get_avatar: function(model, field, id) {
            return this.session.prefix + '/web/binary/image?session_id=' + this.session.session_id + '&model=' + model + '&field=' + field + '&id=' + (id || '');
        },
    });
    
    
    /* Add WallView widget to registry */
    session.web.client_actions.add('mail.all_feeds', 'session.mail.WallView');
    
    /* WallView widget: a wall of messages */
    mail.WallView = session.web.Widget.extend({
        template: 'Wall',

        /**
         * @param {Object} parent parent
         * @param {Object} [params]
         * @param {Number} [params.limit=20] number of messages to show and fetch
         * @param {Number} [params.search_view_id=false] search view id for messages
         * @var {Array} sorted_comments records sorted by res_model and res_id
         *                  records.res_model = {res_ids}
         *                  records.res_model.res_id = [records]
         */
        init: function (parent, params) {
            this._super(parent);
            this.params = params || {};
            this.params.limit = params.limit || 50;
            this.params.search_view_id = params.search_view_id || false;
            this.params.thread_level = params.thread_level || 1;
            this.params.search = {};
            this.params.domain = [];
            this.sorted_comments = {'models': {}};
            this.display_show_more = true;
            /* DataSets */
            this.ds_msg = new session.web.DataSet(this, 'mail.message');
            this.ds_thread = new session.web.DataSet(this, 'mail.thread');
            this.ds_groups = new session.web.DataSet(this, 'mail.group');
            this.ds_users = new session.web.DataSet(this, 'res.users');
        },

        start: function() {
            var self = this;
            this._super.apply(this, arguments);
            /* events and buttons */
            this.$element.find('button.oe_mail_wall_button_comment').bind('click', function () { self.do_comment(); });
            this.$element.find('button.oe_mail_wall_button_more').bind('click', function () { self.do_more(); });
            this.$element.find('p.oe_mail_wall_nomore').hide();
            /* load mail.message search view */
            var search_view_loaded = this.load_search_view(this.params.search_view_id, {}, false);
            var search_view_ready = $.when(search_view_loaded).then(function () {
                self.searchview.on_search.add(self.do_searchview_search);
            });
            /* fetch comments */
            var comments_ready = this.init_comments(this.params.domain, {}, 0, this.params.limit);
            return (search_view_ready && comments_ready);
        },
        
        stop: function () {
            this._super.apply(this, arguments);
        },

        /**
         * Loads the mail.message search view
         * @param {Number} view_id id of the search view to load
         * @param {Object} defaults ??
         * @param {Boolean} hidden ??
         */
        load_search_view: function (view_id, defaults, hidden) {
            this.searchview = new session.web.SearchView(this, this.ds_msg, view_id || false, defaults || {}, hidden || false);
            return this.searchview.appendTo(this.$element.find('div.oe_mail_wall_search'));
        },

        /**
         * Aggregate the domains, contexts and groupbys in parameter
         * with those from search form, and then calls fetch_comments
         * to actually fetch comments
         * @param {Array} domains
         * @param {Array} contexts
         * @param {Array} groupbys
         */
        do_searchview_search: function(domains, contexts, groupbys) {
            var self = this;
            this.rpc('/web/session/eval_domain_and_context', {
                domains: domains || [],
                contexts: contexts || [],
                group_by_seq: groupbys || []
            }, function (results) {
                self.params.search['context'] = results.context;
                self.params.search['domain'] = results.domain;
                self.params.search['groupby'] = results.group_by;
                self.init_comments(self.params.search['domain'], self.params.search['context']);
            });
        },

        /**
         * Initializes Wall and calls fetch_comments
         * @param {Array} domains
         * @param {Array} contexts
         * @param {Array} groupbys
         * @param {Number} limit number of messages to fetch
         */
        init_comments: function(domain, context, offset, limit) {
            this.params.domain = [];
            this.display_show_more = true;
            this.sorted_comments = {'models': {}};
            this.$element.find('div.oe_mail_wall_threads').empty();
            return this.fetch_comments(domain, context, offset, limit);
        },

        /**
         * Fetches Wall comments (mail.thread.get_pushed_messages)
         * @param {Array} domains
         * @param {Array} contexts
         * @param {Array} groupbys
         * @param {Number} limit number of messages to fetch
         */
        fetch_comments: function (domain, context, offset, limit) {
            var self = this;
            var load_res = this.ds_thread.call('get_pushed_messages', 
                [[this.session.uid], (limit || 2), (offset || 0), (domain || []), true, [false], (context || null)]).then(function (records) {
                    if (records.length < self.params.limit) self.display_show_more = false;
                    self.display_comments(records);
                    if (! self.display_show_more) {
                        self.$element.find('button.oe_mail_wall_button_more:last').hide();
                        self.$element.find('p.oe_mail_wall_nomore:last').show();
                    }
                });
            return load_res;
        },

        /**
         * @param {Array} records records to show in threads
         */
        display_comments: function (records) {
            var sorted_comments = this.sort_comments(records);
            //console.log(sorted_comments);
            var self = this;
            _(sorted_comments.model_list).each(function (model_name) {
                _(sorted_comments.models[model_name].root_ids).each(function (id) {
                    var records = sorted_comments.models[model_name].msgs[id];
                    var template = 'WallThreadContainer';
                    var render_res = session.web.qweb.render(template, {});
                    $('<div class="oe_mail_wall_thread">').html(render_res).appendTo(self.$element.find('div.oe_mail_wall_threads'));
                    var thread = new mail.Thread(self, {
                        'res_model': model_name, 'res_id': records[0]['res_id'], 'uid': self.session.uid, 'records': records,
                        'parent_id': false, 'thread_level': self.params.thread_level, 'show_hide': true}
                        );
                    var thread_displayed = thread.appendTo(self.$element.find('div.oe_mail_wall_thread:last'));
                });
            });
        },

        /**
         * Add records to sorted_comments array
         * @param {Array} records records from mail.message sorted by date desc
         * @returns {Object} sc sorted_comments: dict
         *                      sc.model_list = [record.model names]
         *                      sc.models[model_name] = {
         *                          'root_ids': [root record.ids],
         *                          'id_to_root': {record.id: root.id, ..},
         *                          'msgs': {'root_id': [records]}, still sorted by date desc
         *                          }, for each model
         */
        sort_comments: function (records) {
            var self = this;
            var sc = {'model_list': [], 'models': {}}
            var cur_iter = 0; var max_iter = 10; var modif = true;
            /* step1: get roots */
            while ( modif && (cur_iter++) < max_iter) {
                modif = false;
                _(records).each(function (record) {
                    if (_.indexOf(sc['model_list'], record.model) == -1) {
                        sc['model_list'].push(record.model);
                        sc['models'][record.model] = {'root_ids': [], 'id_to_root': {}, 'msgs': {}};
                    }
                    if (! self.sorted_comments['models'][record.model]) {
                        self.sorted_comments['models'][record.model] = {'root_ids': []};
                    }
                    var rmod = sc['models'][record.model];
                    if (record.parent_id == false && (_.indexOf(rmod['root_ids'], record.id) == -1)) {
                        rmod['root_ids'].push(record.id);
                        rmod['msgs'][record.id] = [];
                        self.sorted_comments['models'][record.model]['root_ids'].push(record.id);
                        modif = true;
                    } 
                    else {
                        if ((_.indexOf(rmod['root_ids'], record.parent_id[0]) != -1)  && (! rmod['id_to_root'][record.id])) {
                             rmod['id_to_root'][record.id] = record.parent_id[0];
                             modif = true;
                        }
                        else if ( rmod['id_to_root'][record.parent_id[0]]  && (! rmod['id_to_root'][record.id])) {
                             rmod['id_to_root'][record.id] = rmod['id_to_root'][record.parent_id[0]];
                             modif = true;
                        }
                    }
                });
            }
            /* step2: add records */
            _(records).each(function (record) {
                var root_id = sc['models'][record.model]['id_to_root'][record.id];
                if (! root_id) root_id = record.id;
                sc['models'][record.model]['msgs'][root_id].push(record);
            });
            return sc;
        },

        /**
         * Create a domain to fetch new comments according to
         * comment already present in sorted_comments
         * @param {Object} sorted_comments (see sort_comments)
         * @returns {Array} fetch_domain (OpenERP domain style)
         */
        get_fetch_domain: function (sorted_comments) {
            var domain = [];
            _(sorted_comments.models).each(function (sc_model, model_name) { //each model
                var ids = [];
                _(sc_model.root_ids).each(function (id) { // each record
                    ids.push(id);
                });
                domain.push('|', ['model', '!=', model_name], '!', ['id', 'child_of', ids]);
            });
            return domain;
        },
        
        /**
         * Action: Shows more discussions
         */
        do_more: function () {
            var domain = this.get_fetch_domain(this.sorted_comments);
            return this.fetch_comments(domain);
        },
        
        /**
         * Action: Posts a comment
         */
        do_comment: function () {
            var body_text = this.$element.find('textarea.oe_mail_wall_action_textarea').val();
            return this.ds_thread.call('message_append_note', [[], 'Tweet', body_text, false, 'comment']).then(this.init_comments());
            //return this.ds_users.call('message_append_note', [[this.session.uid], 'Tweet', body_text, false, 'comment']).then(this.init_comments());
        },
        
        /**
         * Tools: get avatar mini (TODO: should be moved in some tools ?)
         */
        thread_get_mini: function(model, field, id) {
            return this.session.prefix + '/web/binary/image?session_id=' + this.session.session_id + '&model=' + model + '&field=' + field + '&id=' + (id || '');
        },
    });
};

// vim:et fdc=0 fdl=0 foldnestmax=3 fdm=syntax:
