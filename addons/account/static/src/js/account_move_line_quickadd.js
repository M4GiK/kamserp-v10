openerp.account = function (instance) {
    var _t = instance.web._t,
        _lt = instance.web._lt;
    var QWeb = instance.web.qweb;
    
    instance.web.account = {};
    
    instance.web.views.add('tree_account_move_line_quickadd', 'instance.web.account.QuickAddListView');
    instance.web.account.QuickAddListView = instance.web.ListView.extend({
        _template: 'ListView',

        init: function() {
            var self = this;
            this._super.apply(this, arguments);
            this.journals = [];
            this.periods = [];
            this.current_journal = null;
            this.current_period = null;
        },
        load_list: function() {
            var self = this;
            var tmp = this._super.apply(this, arguments);

            this.$el.prepend(QWeb.render("AccountMoveLineQuickAdd", {widget: this}));
            
            this.$("#oe_account_select_journal").change(function() {
                    self.current_journal = parseInt(this.value);
                    self.do_search(self.last_domain, self.last_context, self.last_group_by);
                });
            this.$("#oe_account_select_period").change(function() {
                    self.current_period = parseInt(this.value);
                    self.do_search(self.last_domain, self.last_context, self.last_group_by);
                });
            return tmp;
        },
        do_search: function(domain, context, group_by) {
            var self = this;
            this.last_domain = domain;
            this.last_context = context;
            this.last_group_by = group_by;
            this.old_search = _.bind(this._super, this);
            var mod = new instance.web.Model("account.move.line", context, domain);
            var getarray = [];
            getarray.push(mod.call("list_journals", []).then(function(result) {
                self.journals = result;
            }));
            getarray.push(mod.call("list_periods", []).then(function(result) {
                self.periods = result;
            }));
            $.when.apply($, getarray).done(function () {
                self.current_journal = self.current_journal === null ? self.journals[0][0] : self.current_journal;
                self.current_period = self.current_period === null ? self.periods[0][0] :self.current_period;
                var tmp = self.search_by_journal_period();
            });
        },
        search_by_journal_period: function() {
            var self = this;
            
            compoundDomain = new instance.web.CompoundDomain(self.last_domain, 
                [
                ["journal_id", "=", self.current_journal], 
                ["period_id", "=", self.current_period] 
                ]);
            self.last_context["journal_id"] = self.current_journal;
            self.last_context["period_id"] = self.current_period;
            return self.old_search(compoundDomain, self.last_context, self.last_group_by);
        },
        _next: function (next_record, options) {
            next_record = next_record || 'succ';
            var self = this;
            return this.save_edition().then(function (saveInfo) {
                if (saveInfo.created || self.records.at(self.records.length-1).get("id") === saveInfo.record.get("id")) {
                    return self.start_edition();
                }
                var record = self.records[next_record](
                        saveInfo.record, {wraparound: true});
                return self.start_edition(record, options);
            });
        },
    });
};
