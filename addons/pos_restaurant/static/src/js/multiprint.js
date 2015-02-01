openerp.pos_restaurant.load_multiprint = function(instance,module){
    var QWeb = instance.web.qweb;
	var _t = instance.web._t;

    module.Printer = instance.web.Class.extend(openerp.PropertiesMixin,{
        init: function(parent,options){
            openerp.PropertiesMixin.init.call(this,parent);
            var self = this;
            options = options || {};
            var url = options.url || 'http://localhost:8069';
            this.connection = new instance.web.Session(undefined,url, { use_cors: true});
            this.host       = url;
            this.receipt_queue = [];
        },
        print: function(receipt){
            var self = this;
            if(receipt){
                this.receipt_queue.push(receipt);
            }
            var aborted = false;
            function send_printing_job(){
                if(self.receipt_queue.length > 0){
                    var r = self.receipt_queue.shift();
                    self.connection.rpc('/hw_proxy/print_xml_receipt',{receipt: r},{timeout: 5000})
                        .then(function(){
                            send_printing_job();
                        },function(){
                            self.receipt_queue.unshift(r);
                        });
                }
            }
            send_printing_job();
        },
    });

    module.load_models({
        model: 'restaurant.printer',
        fields: ['name','proxy_ip','product_categories_ids'],
        domain: null,
        loaded: function(self,printers){
            var active_printers = {};
            for (var i = 0; i < self.config.printer_ids.length; i++) {
                active_printers[self.config.printer_ids[i]] = true;
            }

            self.printers = [];
            for(var i = 0; i < printers.length; i++){
                if(active_printers[printers[i].id]){
                    var printer = new module.Printer(self,{url:'http://'+printers[i].proxy_ip+':8069'});
                    printer.config = printers[i];
                    self.printers.push(printer);
                }
            }
        },
    });

    var _super_orderline = module.Orderline.prototype;
    module.Orderline = module.Orderline.extend({
        initialize: function(args) {
            _super_orderline.initialize.apply(this,arguments);
            if (typeof this.mp_dirty === 'undefined') {
                // mp dirty is true if this orderline has changed
                // since the last kitchen print
                this.mp_dirty = true;
            } 
            if (!this.mp_skip) {
                // mp_skip is true if the cashier want this orderline
                // not to be sent to the kitchen
                this.mp_skip  = false;
            }
        },
        init_from_JSON: function(json) {
            _super_orderline.init_from_JSON.apply(this,arguments);
            this.mp_dirty = json.mp_dirty;
            this.mp_skip  = json.mp_skip;
        },
        export_as_JSON: function() {
            var json = _super_orderline.export_as_JSON.apply(this,arguments);
            json.mp_dirty = this.mp_dirty;
            json.mp_skip  = this.mp_skip;
            return json;
        },
        set_quantity: function(quantity) {
            if (quantity !== this.quantity) {
                this.mp_dirty = true;
            }
            _super_orderline.set_quantity.apply(this,arguments);
        },
        can_be_merged_with: function(orderline) { 
            return (!this.mp_skip) && 
                   (!orderline.mp_skip) &&
                   _super_orderline.can_be_merged_with.apply(this,arguments);
        },
        set_skip: function(skip) {
            if (this.mp_dirty && skip && !this.mp_skip) {
                this.mp_skip = true;
                this.trigger('change',this);
            }
            if (this.mp_skip && !skip) {
                this.mp_dirty = true;
                this.mp_skip  = false;
                this.trigger('change',this);
            }
        },
        set_dirty: function(dirty) {
            this.mp_dirty = dirty;
            this.trigger('change',this);
        },
        get_line_diff_hash: function(){
            if (this.get_note()) {
                return this.get_product().id + '|' + this.get_note();
            } else {
                return '' + this.get_product().id;
            }
        },
    });

    module.OrderWidget.include({
        render_orderline: function(orderline) {
            var node = this._super(orderline);
            if (orderline.mp_skip) {
                node.classList.add('skip');
            } else if (orderline.mp_dirty) {
                node.classList.add('dirty');
            }
            return node;
        },
        click_line: function(line, event) {
            if (this.pos.get_order().selected_orderline !== line) {
                this.mp_dbclk_time = (new Date()).getTime();
            } else if (!this.mp_dbclk_time) {
                this.mp_dbclk_time = (new Date()).getTime();
            } else if (this.mp_dbclk_time + 500 > (new Date()).getTime()) {
                line.set_skip(!line.mp_skip);
                this.mp_dbclk_time = 0;
            } else {
                this.mp_dbclk_time = (new Date()).getTime();
            }
            this._super(line, event);
        },
    });

    var _super_order = module.Order.prototype;
    module.Order = module.Order.extend({
        build_line_resume: function(){
            var resume = {};
            this.orderlines.each(function(line){
                if (line.mp_skip) {
                    return;
                }
                var line_hash = line.get_line_diff_hash();
                var qty  = Number(line.get_quantity());
                var note = line.get_note();
                var product_id = line.get_product().id;

                if (typeof resume[line_hash] === 'undefined') {
                    resume[line_hash] = { qty: qty, note: note, product_id: product_id };
                } else {
                    resume[line_hash].qty += qty;
                }

            });
            return resume;
        },
        saveChanges: function(){
            this.saved_resume = this.build_line_resume();
            this.orderlines.each(function(line){
                line.set_dirty(false);
            });
            this.trigger('change',this);
        },
        computeChanges: function(categories){
            var current_res = this.build_line_resume();
            var old_res     = this.saved_resume || {};
            var json        = this.export_as_JSON();
            var add = [];
            var rem = [];

            for ( line_hash in current_res) {
                var curr = current_res[line_hash];
                var old  = old_res[line_hash];

                if (typeof old === 'undefined') {
                    add.push({
                        'id':       curr.product_id,
                        'name':     this.pos.db.get_product_by_id(curr.product_id).display_name,
                        'note':     curr.note,
                        'qty':      curr.qty,
                    });
                } else if (old.qty < curr.qty) {
                    add.push({
                        'id':       curr.product_id,
                        'name':     this.pos.db.get_product_by_id(curr.product_id).display_name,
                        'note':     curr.note,
                        'qty':      curr.qty - old.qty,
                    });
                } else if (old.qty > curr.qty) {
                    rem.push({
                        'id':       curr.product_id,
                        'name':     this.pos.db.get_product_by_id(curr.product_id).display_name,
                        'note':     curr.note,
                        'qty':      old.qty - curr.qty,
                    });
                }
            }

            for (line_hash in old_res) {
                if (typeof current_res[line_hash] === 'undefined') {
                    var old = old_res[line_hash];
                    rem.push({
                        'id':       old.product_id,
                        'name':     this.pos.db.get_product_by_id(old.product_id).display_name,
                        'note':     old.note,
                        'qty':      old.qty, 
                    });
                }
            }

            if(categories && categories.length > 0){
                // filter the added and removed orders to only contains
                // products that belong to one of the categories supplied as a parameter

                var self = this;
                function product_in_category(product_id){
                    var cat = self.pos.db.get_product_by_id(product_id).pos_categ_id[0];
                    while(cat){
                        for(var i = 0; i < categories.length; i++){
                            if(cat === categories[i]){
                                return true;
                            }
                        }
                        cat = self.pos.db.get_category_parent_id(cat);
                    }
                    return false;
                }

                var _add = [];
                var _rem = [];
                
                for(var i = 0; i < add.length; i++){
                    if(product_in_category(add[i].id)){
                        _add.push(add[i]);
                    }
                }
                add = _add;

                for(var i = 0; i < rem.length; i++){
                    if(product_in_category(rem[i].id)){
                        _rem.push(rem[i]);
                    }
                }
                rem = _rem;
            }

            var d = new Date();
            var hours   = '' + d.getHours();
                hours   = hours.length < 2 ? ('0' + hours) : hours;
            var minutes = '' + d.getMinutes();
                minutes = minutes.length < 2 ? ('0' + minutes) : minutes;

            return {
                'new': add,
                'cancelled': rem,
                'table': json.table || false,
                'floor': json.floor || false,
                'name': json.name  || 'unknown order',
                'time': {
                    'hours':   hours,
                    'minutes': minutes,
                },
            };
            
        },
        printChanges: function(){
            var printers = this.pos.printers;
            for(var i = 0; i < printers.length; i++){
                var changes = this.computeChanges(printers[i].config.product_categories_ids);
                if ( changes['new'].length > 0 || changes['cancelled'].length > 0){
                    var receipt = QWeb.render('OrderChangeReceipt',{changes:changes, widget:this});
                    printers[i].print(receipt);
                }
            }
        },
        hasChangesToPrint: function(){
            var printers = this.pos.printers;
            for(var i = 0; i < printers.length; i++){
                var changes = this.computeChanges(printers[i].config.product_categories_ids);
                if ( changes['new'].length > 0 || changes['cancelled'].length > 0){
                    return true;
                }
            }
            return false;
        },
        export_as_JSON: function(){
            var json = _super_order.export_as_JSON.apply(this,arguments);
            json.multiprint_resume = this.saved_resume;
            return json;
        },
        init_from_JSON: function(json){
            _super_order.init_from_JSON.apply(this,arguments);
            this.saved_resume = json.multiprint_resume;
        },
    });

    module.SubmitOrderButton = module.ActionButtonWidget.extend({
        'template': 'SubmitOrderButton',
        button_click: function(){
            var order = this.pos.get_order();
            if(order.hasChangesToPrint()){
                order.printChanges();
                order.saveChanges();
            }
        },
    });

    module.define_action_button({
        'name': 'submit_order',
        'widget': module.SubmitOrderButton,
        'condition': function() {
            return this.pos.printers.length;
        },
    });

    module.OrderWidget.include({
        update_summary: function(){
            this._super();
            var changes = this.pos.get_order().hasChangesToPrint();
            if (this.getParent().action_buttons && 
                this.getParent().action_buttons.submit_order) {
                this.getParent().action_buttons.submit_order.highlight(changes);
            }
        },
    });

};

